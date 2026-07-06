"""Configuration for backend_flask application.

Values are read from environment variables with sensible defaults for
local development.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).parent

# ML service endpoint
ML_SERVICE_URL = os.environ.get('ML_SERVICE_URL', 'http://localhost:8000')

# Uploads / generated paths
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', str(BASE_DIR / '..' / 'uploads'))
GENERATED_DIR = os.environ.get('GENERATED_DIR', str(BASE_DIR / '..' / 'generated'))
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024 # 10 MB
MAX_TOTAL_CHARS = 5000000 # 5 million characters

# Database
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'flashcard_db')
MONGO_COLLECTION = os.environ.get('MONGO_COLLECTION', 'flashcards')

# Server
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('1', 'true', 'yes')

# Auth & Rate Limiting
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-dev-secret-key')
RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '10 per hour')
RATE_LIMIT_STORAGE = os.environ.get('RATE_LIMIT_STORAGE', 'memory://')

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

# Misc
DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', 50))
# Whether to persist generated records to a local JSONL file when Mongo is
# unavailable. Default: False to avoid creating repo files during local dev.
ENABLE_FILE_DB = os.environ.get('ENABLE_FILE_DB', 'False').lower() in ('1', 'true', 'yes')
