#!/usr/bin/env bash
echo "Starting ML service on http://0.0.0.0:8000"
uvicorn ml_service.app:app --host 0.0.0.0 --port 8000
