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
ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "txt"}
MAX_TOTAL_CHARS = getattr(config_mod, 'MAX_TOTAL_CHARS', 80000)
MAX_Q_TOTAL = getattr(config_mod, 'MAX_Q_TOTAL', 25)
UPLOAD_FOLDER = getattr(config_mod, 'UPLOAD_FOLDER', 'uploads')
MODEL_DIR = getattr(config_mod, 'MODEL_DIR', None)
ML_SERVICE_URL = getattr(config_mod, 'ML_SERVICE_URL', None)
FILE_SIZE_LIMIT = getattr(config_mod, 'MAX_UPLOAD_SIZE_BYTES', 50 * 1024 * 1024)


def _allowed_file(filename: str) -> bool:
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def _save_uploaded_file(storage_file) -> Tuple[str, str]:
    filename = secure_filename(storage_file.filename)
    out_dir = UPLOAD_FOLDER
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, f"{int(time.time())}_{filename}")
    storage_file.save(filepath)
    return filename, filepath



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
    if 'file' not in request.files:
        return jsonify({'error': 'missing file field'}), 400

    storage_file = request.files['file']
    if storage_file.filename == '':
        return jsonify({'error': 'empty filename'}), 400

    if not _allowed_file(storage_file.filename):
        return jsonify({'error': 'unsupported media type'}), 415

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

    if db_service.check_duplicate(storage_file.filename, created_by):
        return jsonify({'error': 'Duplicate document upload not allowed.'}), 400



    # File size limit
    storage_file.stream.seek(0, os.SEEK_END)
    size = storage_file.stream.tell()
    storage_file.stream.seek(0)
    if FILE_SIZE_LIMIT and size > FILE_SIZE_LIMIT:
        return jsonify({'error': 'file too large'}), 413

    # Save file to disk
    try:
        filename, filepath = _save_uploaded_file(storage_file)
    except Exception as e:
        logger.exception("Failed to save uploaded file: %s", e)
        return jsonify({'error': 'failed to save file'}), 500

    # Extract chunks using improved file_service
    try:
        chunks = file_service.extract_text_chunks(filepath, max_chunk_chars=2000, overlap_chars=200)
    except Exception as e:
        logger.exception("Chunk extraction failed: %s", e)
        return jsonify({'error': 'failed to extract text from file'}), 500

    if not chunks:
        return jsonify({'error': 'no text could be extracted from the document'}), 400

    total_chars = sum(len(c.get('text', '')) for c in chunks)
    if total_chars > MAX_TOTAL_CHARS:
        return jsonify({'error': 'document too large; reduce size or split'}), 413

    chunks_processed = len(chunks)
    model_version = 'openrouter_gpt-4o'
    record: Dict[str, Any] = {
        'source_file': filename,
        'path': filepath,
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

    sample = aggregated[:6]
    return jsonify({'status': 'ok', 'record_id': str(saved_id), 'flashcards': sample, 'total_flashcards': len(aggregated)}), 200


@upload_bp.route('/regenerate/<record_id>', methods=['POST'])
@jwt_required()
def regenerate(record_id: str):
    """POST /regenerate/<record_id>
    Regenerates flashcards for an existing document record.
    """
    record = db_service.get_record_by_id(record_id)
    if not record:
        return jsonify({'error': 'record not found'}), 404
        
    filepath = record.get('path')
    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': 'original file not found'}), 404
        
    try:
        chunks = file_service.extract_text_chunks(filepath, max_chunk_chars=2000, overlap_chars=200)
    except Exception as e:
        logger.exception("Chunk extraction failed: %s", e)
        return jsonify({'error': 'failed to extract text from file'}), 500
        
    full_text = "\n\n".join(c.get('text', '') for c in chunks)
    max_q_total = getattr(config_mod, 'MAX_Q_TOTAL', MAX_Q_TOTAL)
    
    try:
        aggregated = ai_service.generate_flashcards(full_text, max_q=max_q_total)
    except Exception as e:
        logger.exception("AI Flashcard generation failed during regeneration: %s", e)
        return jsonify({'error': 'AI Generation failed'}), 500
        
    # Update record
    record['flashcards'] = aggregated
    record['stats']['flashcards_generated'] = len(aggregated)
    db_service.save_generated(record) # Should upsert or replace
    
    return jsonify({'status': 'ok', 'flashcards': aggregated}), 200
