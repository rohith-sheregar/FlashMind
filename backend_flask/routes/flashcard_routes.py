from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

# Support both package and script execution
try:
    from backend_flask.services import db_service
    from backend_flask.config import DEFAULT_PAGE_SIZE
except ModuleNotFoundError:
    from services import db_service
    from config import DEFAULT_PAGE_SIZE

flashcard_bp = Blueprint('flashcard_bp', __name__)


@flashcard_bp.route('/list-generated', methods=['GET'])
@jwt_required()
def list_generated():
    try:
        current_user = get_jwt_identity()
        # allow optional ?limit= param
        limit = int(request.args.get('limit', DEFAULT_PAGE_SIZE))
        records = db_service.list_generated(limit=limit, username=current_user)
        return jsonify(records)
    except Exception as e:
        # return empty list with 500 for visibility
        return jsonify({'error': str(e), 'records': []}), 500

