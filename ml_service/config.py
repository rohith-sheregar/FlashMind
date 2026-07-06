"""Configuration settings for the ML service."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent

# API configuration
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))