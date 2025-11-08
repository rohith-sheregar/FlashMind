"""Configuration for backend_flask application.

Values are read from environment variables with sensible defaults for
local development.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ML service endpoint
ML_SERVICE_URL = os.environ.get('ML_SERVICE_URL', 'http://localhost:8000/generate')

# Uploads / generated paths
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', str(BASE_DIR / '..' / 'uploads'))
GENERATED_DIR = os.environ.get('GENERATED_DIR', str(BASE_DIR / '..' / 'generated'))

# Database
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'flashcard_db')
MONGO_COLLECTION = os.environ.get('MONGO_COLLECTION', 'flashcards')

# Server
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('1', 'true', 'yes')

# Misc
DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', 50))
# Whether to persist generated records to a local JSONL file when Mongo is
# unavailable. Default: False to avoid creating repo files during local dev.
ENABLE_FILE_DB = os.environ.get('ENABLE_FILE_DB', 'False').lower() in ('1', 'true', 'yes')
