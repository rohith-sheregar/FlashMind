"""Configuration settings for the ML service."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "model"
DATA_DIR = BASE_DIR / "data"

# Model configuration
DEFAULT_MODEL_PATH = MODEL_DIR / "flashcard_finetuned"
FALLBACK_MODEL = "t5-small"
MAX_INPUT_LENGTH = 512
MAX_OUTPUT_LENGTH = 256
TEMPERATURE = 0.7
NUM_BEAMS = 2

# Training configuration
TRAINING_CONFIG = {
    "batch_size": 8,
    "num_epochs": 3,
    "learning_rate": 3e-5,
    "max_input_length": 256,
    "max_output_length": 256,
    "warmup_steps": 100,
    "weight_decay": 0.01,
    "save_total_limit": 2,
    "logging_steps": 10,
    "evaluation_steps": 500,
    "save_steps": 1000,
}

# Keyword extraction
KEYWORD_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MAX_KEYWORDS = 5
KEYWORD_MIN_LENGTH = 3

# API configuration
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))
MAX_QUESTIONS = 10