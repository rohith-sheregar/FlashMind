Academic Flashcard Generator - Runnable Minimal Setup
----------------------------------------------------
This package contains:
- backend_flask: Flask app that accepts file uploads and calls the ML microservice.
- ml_service: FastAPI microservice that generates flashcards from text.

Quick start (after unzipping):
1. Create and activate a Python virtual environment in two terminals (one for backend, one for ml service).
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
2. Install backend dependencies and run backend:
   cd backend_flask
   pip install -r requirements.txt
   python app.py
3. In a second terminal, install ml service deps and run it:
   cd ml_service
   pip install -r requirements.txt
   uvicorn app:app --host 0.0.0.0 --port 8000
4. Open http://localhost:5000 in your browser and upload a PDF/DOCX/PPTX (or a .txt).

Notes:
- The ML microservice uses Hugging Face transformers by default. On first run it may download model weights (internet required).
- If transformers are unavailable, a fallback simple rule-based generator will be used.


Additional features added:
- train_model.py in ml_service/scripts for fine-tuning a T5 model using a JSONL training file.
- MongoDB persistence support in backend (optional) via MONGO_URI env var.
- Enhanced generator using transformers + KeyBERT for keyword extraction with fallback.
