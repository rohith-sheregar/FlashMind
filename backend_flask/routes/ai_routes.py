from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

try:
    from backend_flask.services import ai_service
    from backend_flask.services.db_service import get_record_by_id, check_generation_limit
    from backend_flask.config import DAILY_GENERATION_LIMIT
except ModuleNotFoundError:
    from services import ai_service
    from services.db_service import get_record_by_id, check_generation_limit
    from config import DAILY_GENERATION_LIMIT

ai_bp = Blueprint('ai_bp', __name__)

import os
import logging
logger = logging.getLogger(__name__)

log_path = 'ai_debug.log'
if os.path.isdir('backend_flask'):
    log_path = 'backend_flask/ai_debug.log'

try:
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
except Exception as e:
    # Fallback to console logging if file writing is unavailable
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

logger.setLevel(logging.INFO)

def process_ai_request(action_func, field_name=None):
    """Helper to check limits, fetch document, and call the AI service."""
    current_user = get_jwt_identity()
    logger.info(f"Starting process_ai_request for user {current_user}, field {field_name}")
    
    # Removed AI limit for testing
    # if not check_and_increment_ai_limit(current_user):
    #     return jsonify({'error': 'Daily OpenRouter API limit reached (2 per day). Please try again tomorrow.'}), 429

    try:
        from backend_flask.services.db_service import save_generated
    except ModuleNotFoundError:
        from services.db_service import save_generated

    data = request.get_json()
    record_id = data.get('record_id')
    logger.info(f"Request data received, record_id: {record_id}")
    if not record_id:
        return jsonify({'error': 'record_id is required'}), 400

    record = get_record_by_id(record_id)
    logger.info(f"Record fetched: {bool(record)}")
    if not record or record.get('created_by') != current_user:
        return jsonify({'error': 'Document not found'}), 404
        
    force_regenerate = bool(data.get('force'))

    # Check if the field already exists (cached)
    if field_name and field_name in record and record[field_name] and not force_regenerate:
        logger.info(f"Returning cached data for {field_name}")
        return jsonify({'data': record[field_name]}), 200

    current_user = get_jwt_identity()
    try:
        from backend_flask.services.db_service import check_generation_limit, increment_generation_count
    except ModuleNotFoundError:
        from services.db_service import check_generation_limit, increment_generation_count
        
    logger.info("Checking generation limits...")
    if not check_generation_limit(current_user, limit=DAILY_GENERATION_LIMIT):
        return jsonify({'error': 'You have reached your daily limit quota. Come back tomorrow!'}), 429

    filepaths = record.get('paths') or ([record.get('path')] if record.get('path') else [])
    logger.info(f"File paths: {filepaths}")
    if not filepaths:
        return jsonify({'error': 'Document file path missing'}), 404

    logger.info("Extracting document text...")
    text = ai_service.get_document_text(filepaths)
    logger.info(f"Text extracted, length: {len(text) if text else 0}")
    if not text:
        return jsonify({'error': 'Could not extract text from document'}), 500

    try:
        logger.info(f"Calling action_func for {field_name}...")
        result = action_func(text)
        logger.info(f"action_func completed for {field_name}")
        
        # Save to database
        if field_name:
            record[field_name] = result
            save_generated(record)
            logger.info("Result saved to database")
            increment_generation_count(current_user)
            
        return jsonify({'data': result}), 200
    except ValueError as ve:
        logger.error(f"ValueError in {field_name}: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Exception in {field_name}: {e}")
        return jsonify({'error': 'AI Generation failed: ' + str(e)}), 500


@ai_bp.route('/generate-quiz', methods=['POST'])
@jwt_required()
def generate_quiz_route():
    return process_ai_request(ai_service.generate_quiz, 'quiz')


@ai_bp.route('/generate-mindmap', methods=['POST'])
@jwt_required()
def generate_mindmap_route():
    return process_ai_request(ai_service.generate_mindmap, 'mindmap')


@ai_bp.route('/extract-topics', methods=['POST'])
@jwt_required()
def extract_topics_route():
    return process_ai_request(ai_service.extract_topics, 'topics')

@ai_bp.route('/generate-flashcards', methods=['POST'])
@jwt_required()
def generate_flashcards_route():
    return process_ai_request(ai_service.generate_flashcards, 'flashcards')
