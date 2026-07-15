import re
import datetime
import logging
from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

try:
    from backend_flask.services.db_service import get_mongo_client, MONGO_DB_NAME, get_user_generation_count
    from backend_flask.services.email_service import generate_otp, send_otp_email
    from backend_flask.config import DAILY_GENERATION_LIMIT
except ModuleNotFoundError:
    from services.db_service import get_mongo_client, MONGO_DB_NAME, get_user_generation_count
    from services.email_service import generate_otp, send_otp_email
    from config import DAILY_GENERATION_LIMIT

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Email regex pattern
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
OTP_EXPIRY_MINUTES = 5


def get_db():
    client = get_mongo_client()
    return client.get_database(MONGO_DB_NAME)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Step 1: Validate inputs, send OTP to email."""
    data = request.get_json()
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    # --- Validation ---
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({'error': 'Please enter a valid email address'}), 400

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500

    users_collection = db['users']

    # Check username uniqueness
    if users_collection.find_one({'username': username}):
        return jsonify({'error': 'Username already exists'}), 400

    # Check email uniqueness
    if users_collection.find_one({'email': email}):
        return jsonify({'error': 'This email is already registered'}), 400

    # --- Generate and store OTP ---
    otp = generate_otp()
    pending_collection = db['pending_otps']

    # Remove any previous pending OTP for this email
    pending_collection.delete_many({'email': email})

    # Hash the password now so we don't store plaintext even temporarily
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    pending_collection.insert_one({
        'username': username,
        'email': email,
        'password': hashed_password,
        'otp': otp,
        'created_at': datetime.datetime.utcnow(),
        'expires_at': datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES)
    })

    # Create TTL index (idempotent — only creates if doesn't exist)
    pending_collection.create_index('expires_at', expireAfterSeconds=0)

    # --- Send OTP email ---
    if not send_otp_email(email, otp):
        # DEV FALLBACK: If email sending fails (e.g., SMTP blocked on Render Free Tier),
        # log the OTP to the console so the developer can retrieve it from the Render dashboard.
        logger.warning(f"--- [DEVELOPER FALLBACK] ---")
        logger.warning(f"SMTP failed to send email to {email}. You can bypass this by copying the code below.")
        logger.warning(f"YOUR VERIFICATION OTP: {otp}")
        logger.warning(f"----------------------------")
        return jsonify({'message': 'OTP generated. (Render Free Tier: check server console logs for the 6-digit code)'}), 200

    return jsonify({'message': 'OTP sent to your email. Please verify to complete registration.'}), 200


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Step 2: Verify OTP and create the user account."""
    data = request.get_json()
    email = (data.get('email') or '').strip().lower()
    otp = (data.get('otp') or '').strip()

    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), 400

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500

    pending_collection = db['pending_otps']
    pending = pending_collection.find_one({'email': email})

    if not pending:
        return jsonify({'error': 'No pending verification found. Please register again.'}), 400

    # Check expiry
    if datetime.datetime.utcnow() > pending['expires_at']:
        pending_collection.delete_many({'email': email})
        return jsonify({'error': 'OTP has expired. Please register again.'}), 400

    # Verify OTP
    if pending['otp'] != otp:
        return jsonify({'error': 'Invalid OTP. Please try again.'}), 400

    # --- Create user account ---
    users_collection = db['users']

    # Double-check uniqueness (race condition guard)
    if users_collection.find_one({'username': pending['username']}):
        pending_collection.delete_many({'email': email})
        return jsonify({'error': 'Username was taken while verifying. Please register again.'}), 400

    if users_collection.find_one({'email': email}):
        pending_collection.delete_many({'email': email})
        return jsonify({'error': 'Email was registered while verifying. Please try logging in.'}), 400

    users_collection.insert_one({
        'username': pending['username'],
        'email': email,
        'password': pending['password'],
        'created_at': datetime.datetime.utcnow(),
        'email_verified': True
    })

    # Cleanup
    pending_collection.delete_many({'email': email})

    return jsonify({'message': 'Email verified! Your account has been created successfully.'}), 201


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP for a pending registration."""
    data = request.get_json()
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    db = get_db()
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500

    pending_collection = db['pending_otps']
    pending = pending_collection.find_one({'email': email})

    if not pending:
        return jsonify({'error': 'No pending registration found. Please register first.'}), 400

    # Generate new OTP
    new_otp = generate_otp()
    pending_collection.update_one(
        {'email': email},
        {
            '$set': {
                'otp': new_otp,
                'created_at': datetime.datetime.utcnow(),
                'expires_at': datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES)
            }
        }
    )

    if not send_otp_email(email, new_otp):
        # DEV FALLBACK: If email sending fails (e.g., SMTP blocked on Render Free Tier),
        # log the OTP to the console so the developer can retrieve it from the Render dashboard.
        logger.warning(f"--- [DEVELOPER FALLBACK - RESEND] ---")
        logger.warning(f"SMTP failed to resend email to {email}. You can bypass this by copying the code below.")
        logger.warning(f"YOUR NEW VERIFICATION OTP: {new_otp}")
        logger.warning(f"-------------------------------------")
        return jsonify({'message': 'A new OTP has been generated. (Render Free Tier: check server console logs for the 6-digit code)'}), 200

    return jsonify({'message': 'A new OTP has been sent to your email.'}), 200


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


@auth_bp.route('/status', methods=['GET'])
@jwt_required()
def user_status():
    current_user = get_jwt_identity()
    count = get_user_generation_count(current_user)
    return jsonify({'generations_used': count, 'limit': DAILY_GENERATION_LIMIT}), 200
