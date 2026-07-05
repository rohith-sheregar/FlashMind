from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token

try:
    from backend_flask.services.db_service import get_mongo_client, MONGO_DB_NAME
except ModuleNotFoundError:
    from services.db_service import get_mongo_client, MONGO_DB_NAME

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

def get_db():
    client = get_mongo_client()
    return client.get_database(MONGO_DB_NAME)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    
    users_collection = db['users']
    if users_collection.find_one({'username': username}):
        return jsonify({'error': 'Username already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    users_collection.insert_one({'username': username, 'password': hashed_password})
    
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500

    users_collection = db['users']
    user = users_collection.find_one({'username': username})
    
    if user and bcrypt.check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username)
        return jsonify({'access_token': access_token, 'username': username}), 200

    return jsonify({'error': 'Invalid credentials'}), 401

from flask_jwt_extended import jwt_required, get_jwt_identity
try:
    from backend_flask.services.db_service import get_user_generation_count
except ModuleNotFoundError:
    from services.db_service import get_user_generation_count

@auth_bp.route('/status', methods=['GET'])
@jwt_required()
def user_status():
    current_user = get_jwt_identity()
    count = get_user_generation_count(current_user)
    return jsonify({'generations_used': count, 'limit': 5}), 200
