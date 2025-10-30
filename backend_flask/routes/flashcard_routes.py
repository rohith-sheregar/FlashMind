from flask import Blueprint, jsonify, request
try:
    from backend_flask.services import db_service
    from backend_flask.config import DEFAULT_PAGE_SIZE
except ModuleNotFoundError:
    from services import db_service
    from config import DEFAULT_PAGE_SIZE

flashcard_bp = Blueprint('flashcard_bp', __name__)


@flashcard_bp.route('/list-generated', methods=['GET'])
def list_generated():
    try:
        # allow optional ?limit= param
        limit = int(request.args.get('limit', DEFAULT_PAGE_SIZE))
        records = db_service.list_generated(limit=limit)
        return jsonify(records)
    except Exception as e:
        # return empty list with 500 for visibility
        return jsonify({'error': str(e), 'records': []}), 500
