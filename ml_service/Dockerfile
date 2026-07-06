FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a script to download the models at build time so the container starts faster
RUN python -c "\
from sentence_transformers import SentenceTransformer;\
SentenceTransformer('all-MiniLM-L6-v2');\
"

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
