from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

try:
    from backend_flask.services import ai_service
    from backend_flask.services.db_service import get_record_by_id, check_and_increment_ai_limit
except ModuleNotFoundError:
    from services import ai_service
    from services.db_service import get_record_by_id, check_and_increment_ai_limit

ai_bp = Blueprint('ai_bp', __name__)

def process_ai_request(action_func, field_name=None):
    """Helper to check limits, fetch document, and call the AI service."""
    current_user = get_jwt_identity()
    
    # Removed AI limit for testing
    # if not check_and_increment_ai_limit(current_user):
    #     return jsonify({'error': 'Daily OpenRouter API limit reached (2 per day). Please try again tomorrow.'}), 429

    try:
        from backend_flask.services.db_service import save_generated
    except ModuleNotFoundError:
        from services.db_service import save_generated

    data = request.get_json()
    record_id = data.get('record_id')
    if not record_id:
        return jsonify({'error': 'record_id is required'}), 400

    record = get_record_by_id(record_id)
    if not record:
        return jsonify({'error': 'Document not found'}), 404
        
    # Check if the field already exists (cached)
    if field_name and field_name in record and record[field_name]:
        return jsonify({'data': record[field_name]}), 200

    current_user = get_jwt_identity()
    try:
        from backend_flask.services.db_service import check_and_increment_generation
    except ModuleNotFoundError:
        from services.db_service import check_and_increment_generation
        
    if not check_and_increment_generation(current_user, limit=5):
        return jsonify({'error': 'You have reached your limit of 5 AI generations. Please upgrade to premium!'}), 429

    filepath = record.get('path')
    if not filepath:
        return jsonify({'error': 'Document file path missing'}), 404

    text = ai_service.get_document_text(filepath)
    if not text:
        return jsonify({'error': 'Could not extract text from document'}), 500

    try:
        result = action_func(text)
        
        # Save to database
        if field_name:
            record[field_name] = result
            save_generated(record)
            
        return jsonify({'data': result}), 200
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
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
