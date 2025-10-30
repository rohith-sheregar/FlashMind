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

try:
    from backend_flask import config as config_mod
    from backend_flask.services import file_service, db_service
except Exception:
    # When running modules directly from the backend_flask folder (not installed as a package),
    # fall back to local imports.
    try:
        import config as config_mod
        from services import file_service, db_service
    except Exception:
        # As a last resort, raise an informative error
        raise

# Defer importing the ML model manager until needed to avoid heavy imports at module import time.
model_manager_module = None

import requests

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


def _call_model_with_retries(mgr: Optional[Any],
                             text: str,
                             max_q: int,
                             remote_url: Optional[str] = None,
                             attempts: int = 3) -> List[Dict[str, Any]]:
    """Try local manager first; fall back to remote ML service with retries."""
    if mgr is not None:
        try:
            return mgr.generate_from_text(text, max_q=max_q)
        except Exception:
            logger.exception("Local ModelManager.generate_from_text failed; will try remote if configured")

    if not remote_url:
        logger.warning("No remote ML service configured; returning empty list")
        return []

    backoff = 1.0
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.post(remote_url, json={"text": text, "max_q": max_q}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and 'flashcards' in data:
                    return data['flashcards']
                if isinstance(data, list):
                    return data
                logger.warning("Unexpected remote ML response format")
                return []
            else:
                logger.warning("Remote ML returned status %s: %s", resp.status_code, resp.text)
        except requests.RequestException as e:
            logger.warning("Attempt %s: remote ML request failed: %s", attempt, e)
        time.sleep(backoff)
        backoff *= 2

    logger.error("Remote ML service failed after %s attempts", attempts)
    return []


@upload_bp.route('/upload', methods=['POST'])
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
    created_by = form.get('created_by') or request.headers.get('X-User', 'anonymous')

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

    total_chars = sum(len(c.get('text', '')) for c in chunks)
    if total_chars > MAX_TOTAL_CHARS:
        return jsonify({'error': 'document too large; reduce size or split'}), 413

    # Initialize local ModelManager if possible
    mgr: Optional[Any] = None
    try:
        mgr = model_manager_module.load_default_manager(model_dir=MODEL_DIR)
    except Exception:
        logger.warning("Local ModelManager not available; will try remote ML service if configured")
        mgr = None

    aggregated: List[Dict[str, Any]] = []
    seen_pairs = set()
    chunks_processed = 0
    max_q_total = getattr(config_mod, 'MAX_Q_TOTAL', MAX_Q_TOTAL)

    for chunk in chunks:
        text = chunk.get('text', '')
        if not text.strip():
            continue

        requested_chunk_q = requested_max_q

        try:
            fcs_chunk = _call_model_with_retries(mgr, text, requested_chunk_q, remote_url=ML_SERVICE_URL, attempts=3)
        except Exception as e:
            logger.exception("Model call failed for chunk: %s", e)
            fcs_chunk = []

        if not fcs_chunk:
            try:
                if mgr is not None:
                    fcs_chunk = mgr.fallback_rule_based(text, requested_chunk_q)
                else:
                    from ml_service.models.rule_based import enhanced_rule_based_generate as rb
                    fcs_chunk = rb(text, requested_chunk_q)
            except Exception as e:
                logger.exception("Rule-based fallback failed: %s", e)
                fcs_chunk = []

        # Validate with manager if available
        if mgr is not None:
            try:
                fcs_chunk = mgr.validate_flashcards(fcs_chunk)
            except Exception:
                # best-effort normalization
                fcs_chunk = [fc for fc in fcs_chunk if isinstance(fc, dict) and fc.get('question') and fc.get('answer')]

        # Aggregate deduped
        for fc in fcs_chunk:
            q = fc.get('question', '').strip()
            a = fc.get('answer', '').strip()
            if not q or not a:
                continue
            key = (q.lower(), a.lower())
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            aggregated.append(fc)
            if len(aggregated) >= max_q_total:
                break

        chunks_processed += 1
        if len(aggregated) >= max_q_total:
            logger.info("Reached max aggregated flashcards (%s); stopping", max_q_total)
            break

    model_version = getattr(mgr, 'model_dir', None) or ('rule_based' if not mgr else 'unknown')
    record: Dict[str, Any] = {
        'source_file': filename,
        'path': filepath,
        'num_chunks': chunks_processed,
        'flashcards': aggregated,
        'auto_approved': bool(auto_approve),
        'created_by': created_by,
        'model_version': str(model_version),
        'stats': {'flashcards_generated': len(aggregated), 'chunks_processed': chunks_processed}
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


if __name__ == '__main__':
    import argparse
    import pprint

    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True, help='Local file path to simulate upload')
    parser.add_argument('--auto_approve', action='store_true')
    parser.add_argument('--max_q', type=int, default=6)
    parser.add_argument('--created_by', default='cli')
    args = parser.parse_args()

    fp = args.file
    if not os.path.exists(fp):
        print('file not found', fp)
        raise SystemExit(1)

    chunks = file_service.extract_text_chunks(fp, max_chunk_chars=2000, overlap_chars=200)
    print('chunks:', len(chunks))
    try:
        mgr = model_manager_module.load_default_manager(model_dir=MODEL_DIR)
    except Exception as e:
        print('local manager not available:', e)
        mgr = None

    aggregated = []
    for chunk in chunks:
        fcs = _call_model_with_retries(mgr, chunk.get('text', ''), args.max_q, remote_url=ML_SERVICE_URL)
        if not fcs and mgr:
            fcs = mgr.fallback_rule_based(chunk.get('text', ''), args.max_q)
        if mgr:
            fcs = mgr.validate_flashcards(fcs)
        for fc in fcs:
            aggregated.append(fc)
        if len(aggregated) >= MAX_Q_TOTAL:
            break

    record = {
        'source_file': os.path.basename(fp),
        'path': fp,
        'num_chunks': len(chunks),
        'flashcards': aggregated,
        'auto_approved': bool(args.auto_approve),
        'created_by': args.created_by,
        'model_version': getattr(mgr, 'model_dir', 'rule_based') if mgr else 'rule_based',
        'stats': {'flashcards_generated': len(aggregated), 'chunks_processed': len(chunks)}
    }
    print('Saving record via db_service...')
    rid = db_service.save_generated(record)
    print('Saved id:', rid)
    pprint.pprint(record)
