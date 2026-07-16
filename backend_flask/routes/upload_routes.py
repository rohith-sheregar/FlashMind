"""Upload routes for FlashMind backend.

This blueprint implements a production-ready `/upload` endpoint that accepts a
multipart file, extracts cleaned text chunks, invokes a model (local or remote),
aggregates and validates flashcards, and persists the result via `db_service`.

Recommended: add rate-limiting with `flask-limiter` and file scanning / auth in front of this route.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity

# Import config and services. Support both package execution and script
# execution (when __package__ is None). Prefer package imports but fall
# back to local imports when running `python app.py` from inside the
# `backend_flask` directory.
try:
    from backend_flask import config as config_mod
    from backend_flask.services import file_service, db_service
except ModuleNotFoundError:
    # Running as a script from within backend_flask/ -- import locally.
    import config as config_mod
    from services import file_service, db_service

try:
    from backend_flask.services import ai_service
except ModuleNotFoundError:
    from services import ai_service

logger = logging.getLogger(__name__)
upload_bp = Blueprint('upload_bp', __name__)

# Configuration (fall back to config_mod values)
ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "txt", "md", "markdown", "png", "jpg", "jpeg", "webp"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_TOTAL_CHARS = getattr(config_mod, 'MAX_TOTAL_CHARS', 80000)
MAX_Q_TOTAL = getattr(config_mod, 'MAX_Q_TOTAL', 25)
UPLOAD_FOLDER = getattr(config_mod, 'UPLOAD_DIR', getattr(config_mod, 'UPLOAD_FOLDER', 'uploads'))
MODEL_DIR = getattr(config_mod, 'MODEL_DIR', None)
ML_SERVICE_URL = getattr(config_mod, 'ML_SERVICE_URL', None)
FILE_SIZE_LIMIT = getattr(config_mod, 'MAX_UPLOAD_SIZE_BYTES', 10 * 1024 * 1024)
PDF_FILE_SIZE_LIMIT = getattr(config_mod, 'MAX_PDF_UPLOAD_SIZE_BYTES', 10 * 1024 * 1024)
MAX_FILES_PER_DECK = getattr(config_mod, 'MAX_FILES_PER_DECK', 20)


def _extension_for(filename: str) -> str:
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def _allowed_file(filename: str) -> bool:
    ext = _extension_for(filename)
    if not ext:
        return False
    return ext in ALLOWED_EXTENSIONS


def _save_uploaded_file(storage_file) -> Tuple[str, str]:
    filename = secure_filename(storage_file.filename)
    out_dir = UPLOAD_FOLDER
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{filename}")
    storage_file.save(filepath)
    return filename, filepath


def _collect_uploaded_files() -> List[Any]:
    files = request.files.getlist('files')
    if not files:
        files = request.files.getlist('file')
    return [f for f in files if f and f.filename]


def _size_limit_for(filename: str) -> int:
    return PDF_FILE_SIZE_LIMIT if _extension_for(filename) == 'pdf' else FILE_SIZE_LIMIT


def _format_bytes(num_bytes: int) -> str:
    return f"{num_bytes / (1024 * 1024):.0f} MB"


def _uploaded_size(storage_file) -> int:
    storage_file.stream.seek(0, os.SEEK_END)
    size = storage_file.stream.tell()
    storage_file.stream.seek(0)
    return size


def _deck_title_for(files: List[Any], form: Any) -> str:
    requested_title = (form.get('deck_name') or '').strip()
    if requested_title:
        return secure_filename(requested_title) or requested_title

    filenames = [secure_filename(f.filename) for f in files]
    if len(filenames) == 1:
        return filenames[0]

    first_name = filenames[0] or 'uploaded-files'
    first_stem = first_name.rsplit('.', 1)[0]
    if all(_extension_for(name) in IMAGE_EXTENSIONS for name in filenames):
        return f"{first_stem} image deck ({len(filenames)} images)"
    return f"{first_stem} deck ({len(filenames)} files)"


def _paths_for_record(record: Dict[str, Any]) -> List[str]:
    paths = record.get('paths')
    if isinstance(paths, list) and paths:
        return [p for p in paths if p]
    path = record.get('path')
    return [path] if path else []


def _extract_chunks_from_paths(paths: List[str], filenames: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    for idx, filepath in enumerate(paths):
        file_chunks = file_service.extract_text_chunks(filepath, max_chunk_chars=2000, overlap_chars=200)
        source_file = filenames[idx] if filenames and idx < len(filenames) else os.path.basename(filepath)
        for chunk in file_chunks:
            enriched = dict(chunk)
            enriched['source_file'] = source_file
            enriched['source_index'] = idx
            chunks.append(enriched)
    return chunks


@upload_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload() -> Any:
    """POST /upload

    Multipart form-data expected:
      - file: uploaded file (required)
      - auto_approve: 'true'/'false' (optional)
      - max_q: int per chunk (optional)
      - difficulty: 'auto'|'5_marks'|'7_marks'|'9_marks' (optional)
      - created_by: uploader identifier (optional)

    Returns JSON with saved record id and sample flashcards.
    """
    storage_files = _collect_uploaded_files()
    if not storage_files:
        return jsonify({'error': 'missing file field'}), 400

    if len(storage_files) > MAX_FILES_PER_DECK:
        return jsonify({'error': f'upload up to {MAX_FILES_PER_DECK} files per deck'}), 400

    for storage_file in storage_files:
        if storage_file.filename == '':
            return jsonify({'error': 'empty filename'}), 400
        if not _allowed_file(storage_file.filename):
            return jsonify({'error': f'unsupported media type: {storage_file.filename}'}), 415

    # Parse params from form fields (multipart) or JSON body
    form = request.form or {}
    try:
        auto_approve = str(form.get('auto_approve', 'false')).lower() in ('1', 'true', 'yes')
        requested_max_q = int(form.get('max_q', 6))
    except Exception:
        return jsonify({'error': 'invalid parameters'}), 400
    difficulty = form.get('difficulty', 'auto')
    if difficulty not in ('auto', '5_marks', '7_marks', '9_marks'):
        difficulty = 'auto'
    
    current_user = get_jwt_identity()
    created_by = form.get('created_by') or current_user or request.headers.get('X-User', 'anonymous')
    deck_title = _deck_title_for(storage_files, form)

    if db_service.check_duplicate(deck_title, created_by):
        return jsonify({'error': 'Duplicate document upload not allowed.'}), 400



    # Per-file size limits. PDFs are capped at 10 MB by default.
    total_upload_size = 0
    for storage_file in storage_files:
        size = _uploaded_size(storage_file)
        total_upload_size += size
        limit = _size_limit_for(storage_file.filename)
        if limit and size > limit:
            return jsonify({'error': f'{storage_file.filename} is too large; limit is {_format_bytes(limit)}'}), 413

    # Save file(s) to disk
    filenames: List[str] = []
    filepaths: List[str] = []
    try:
        for storage_file in storage_files:
            filename, filepath = _save_uploaded_file(storage_file)
            filenames.append(filename)
            filepaths.append(filepath)
    except Exception as e:
        logger.exception("Failed to save uploaded file: %s", e)
        return jsonify({'error': 'failed to save file'}), 500

    # Extract chunks using improved file_service
    try:
        chunks = _extract_chunks_from_paths(filepaths, filenames)
    except Exception as e:
        logger.exception("Chunk extraction failed: %s", e)
        for filepath in filepaths:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                logger.debug("Failed to clean up upload after extraction error: %s", filepath)
        return jsonify({'error': 'failed to extract text from file'}), 500

    if not chunks:
        return jsonify({'error': 'no text could be extracted from the document'}), 400

    document_text = "\n\n".join(c.get('text', '') for c in chunks if c.get('text'))
    total_chars = len(document_text)
    if total_chars > MAX_TOTAL_CHARS:
        return jsonify({'error': 'document too large; reduce size or split'}), 413

    chunks_processed = len(chunks)
    model_version = 'openrouter_gpt-4o'
    record: Dict[str, Any] = {
        'source_file': deck_title,
        'source_files': filenames,
        'path': filepaths[0],
        'paths': filepaths,
        'file_count': len(filepaths),
        'total_upload_size': total_upload_size,
        'document_text': document_text,
        'num_chunks': chunks_processed,
        'flashcards': [],
        'auto_approved': bool(auto_approve),
        'created_by': created_by,
        'model_version': str(model_version),
        'stats': {'flashcards_generated': 0, 'chunks_processed': chunks_processed}
    }

    try:
        saved_id = db_service.save_generated(record)
        if auto_approve:
            try:
                if hasattr(db_service, 'mark_approved'):
                    db_service.mark_approved(saved_id)
            except Exception:
                logger.debug("mark_approved not available or failed; ensure DB has approved flag")
    except Exception as e:
        logger.exception("Failed to save generated record: %s", e)
        return jsonify({'error': 'failed to save generated flashcards'}), 500

    return jsonify({
        'status': 'ok',
        'record_id': str(saved_id),
        'flashcards': [],
        'total_flashcards': 0,
        'files_uploaded': len(filepaths)
    }), 200


@upload_bp.route('/list', methods=['GET'])
@jwt_required()
def list_records() -> Any:
    """GET /list
    Returns a list of records for the current user.
    """
    current_user = get_jwt_identity()
    records = db_service.list_generated(limit=50, username=current_user)
    
    # Strip heavy data for listing
    for r in records:
        r.pop('document_text', None)
        if 'flashcards' in r and len(r['flashcards']) > 0:
            r['flashcards'] = r['flashcards'][:1]
    
    return jsonify(records)


@upload_bp.route('/documents/<record_id>', methods=['DELETE'])
@jwt_required()
def delete_document(record_id: str) -> Any:
    """DELETE /documents/<record_id>
    Deletes the document and its associated generated data.
    """
    current_user = get_jwt_identity()
    success = db_service.delete_record(record_id, username=current_user)
    if success:
        return jsonify({'message': 'Document deleted successfully'})
    else:
        return jsonify({'error': 'Failed to delete document or unauthorized'}), 400


@upload_bp.route('/regenerate/<record_id>', methods=['POST'])
@jwt_required()
def regenerate(record_id: str):
    """POST /regenerate/<record_id>
    Regenerates flashcards for an existing document record.
    """
    record = db_service.get_record_by_id(record_id)
    if not record:
        return jsonify({'error': 'record not found'}), 404
        
    full_text = record.get('document_text') or ''
    if not full_text:
        filepaths = _paths_for_record(record)
        if not filepaths or any(not os.path.exists(filepath) for filepath in filepaths):
            return jsonify({'error': 'original file not found; please re-upload this document'}), 410

        try:
            chunks = _extract_chunks_from_paths(filepaths, record.get('source_files'))
        except Exception as e:
            logger.exception("Chunk extraction failed: %s", e)
            return jsonify({'error': 'failed to extract text from file'}), 500

        full_text = "\n\n".join(c.get('text', '') for c in chunks)
        record['document_text'] = full_text

    try:
        aggregated = ai_service.generate_flashcards(full_text)
    except Exception as e:
        logger.exception("AI Flashcard generation failed during regeneration: %s", e)
        return jsonify({'error': 'AI Generation failed'}), 500
        
    # Update record
    record['flashcards'] = aggregated
    record['stats']['flashcards_generated'] = len(aggregated)
    db_service.save_generated(record) # Should upsert or replace
    
    return jsonify({'status': 'ok', 'flashcards': aggregated}), 200
