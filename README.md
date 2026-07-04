# 🧠 FlashMind - Academic Flashcard Generator

An intelligent, production-ready flashcard generation system that transforms academic documents (PDFs, DOCX, PPTX, TXT) into exam-ready study materials using advanced NLP and machine learning.

## 🌟 Features

### Document Support
- **Multiple Formats**: PDF, DOCX, PPTX, TXT
- **Smart Text Extraction**: Intelligent parsing with header/footer removal
- **Chunking with Context**: Overlapping text chunks preserve document context
- **Multi-page Handling**: Extracts page numbers and maintains document structure

### AI-Powered Generation
- **Seq2Seq Models**: Fine-tuned T5 transformer for accurate flashcard generation
- **Hybrid Approach**: Combines ML models with rule-based fallbacks
- **Keyword Extraction**: KeyBERT integration for semantic keyword identification
- **Confidence Scoring**: Quality assessment for each generated flashcard

### Production Features
- **Microservice Architecture**: Decoupled Flask backend and FastAPI ML service
- **Database Support**: Optional MongoDB persistence
- **Deduplication**: Prevents duplicate question-answer pairs
- **Validation**: Comprehensive input validation and output sanitization
- **Graceful Fallbacks**: Rule-based generation when ML models are unavailable
- **Drag & Drop UI**: Modern web interface with real-time feedback

## 📋 Project Structure

```
FlashMind/
├── backend_flask/              # Flask web server
│   ├── app.py                 # Application entry point
│   ├── config.py              # Configuration management
│   ├── requirements.txt        # Backend dependencies
│   ├── routes/
│   │   ├── upload_routes.py   # File upload endpoint
│   │   └── flashcard_routes.py # Flashcard retrieval
│   ├── services/
│   │   ├── file_service.py    # Text extraction & chunking
│   │   └── db_service.py      # Database persistence
│   └── static/
│       └── index.html         # Modern React-style UI
│
├── ml_service/                # FastAPI ML microservice
│   ├── app.py                 # API endpoints
│   ├── config.py              # ML configuration
│   ├── requirements.txt        # ML dependencies
│   ├── models/
│   │   ├── model_manager.py   # Model loading & inference
│   │   └── rule_based.py      # Fallback generation
│   └── scripts/
│       └── train_model.py     # Model fine-tuning
│
├── run_backend.sh             # Backend startup script
├── run_ml_service.sh          # ML service startup script
└── README.md                  # This file
```

## 🏗️ Architecture

### Request Flow
```
1. User uploads document (PDF/DOCX/PPTX/TXT)
    ↓
2. Flask backend receives file
    ↓
3. File Service extracts & chunks text
    ↓
4. Text sent to ML Service for generation
    ↓
5. ML Model generates flashcards (or falls back to rule-based)
    ↓
6. Results validated, deduplicated, enriched with keywords
    ↓
7. Saved to MongoDB (optional) and returned to user
```

### Component Details

**Flask Backend (`backend_flask/`)**
- REST API for file uploads and flashcard queries
- Text extraction from multiple document formats
- Chunk-based processing for better context handling
- Integration with MongoDB for persistence
- HTML/CSS/JS frontend served directly

**ML Service (`ml_service/`)**
- FastAPI microservice running on port 8000
- T5 seq2seq model for flashcard generation
- KeyBERT for keyword extraction
- Rule-based fallback generator
- Robust error handling and recovery

**File Service**
- Extracts text from PDF (PyMuPDF), DOCX, PPTX, TXT
- Removes headers, footers, page numbers automatically
- Merges short paragraphs intelligently
- Creates overlapping chunks for better context preservation
- Detects document structure (headings, sections)

**Model Manager**
- Loads fine-tuned T5 models from local cache
- Falls back to `t5-small` if fine-tuned model unavailable
- Implements robust output parsing (JSON, Q&A formats)
- Validates and sanitizes generated flashcards
- Scores confidence for each flashcard

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip or conda
- 50MB+ free disk space for ML models (first run)

### Installation & Running

#### Option 1: Using Shell Scripts (Recommended)

```bash
# Terminal 1 - Backend
./run_backend.sh

# Terminal 2 - ML Service  
./run_ml_service.sh

# Open http://localhost:5000 in your browser
```

#### Option 2: Manual Setup

```bash
# Terminal 1 - Backend
cd backend_flask
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m backend_flask.app

# Terminal 2 - ML Service
cd ml_service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m ml_service.app
# Or with uvicorn directly:
# uvicorn ml_service.app:app --host 0.0.0.0 --port 8000
```

#### Option 3: Docker (Coming Soon)
```bash
docker-compose up
```

### First Time Setup

On first run, the ML service will download model weights (~1-2 GB):
- **T5 Model**: `t5-small` or fine-tuned version
- **Sentence Transformers**: `all-MiniLM-L6-v2` for KeyBERT
- **NLTK Data**: English stopwords and tokenizers

This requires internet access and takes a few minutes.

## 📖 Usage

### Web UI
1. Open http://localhost:5000
2. Drag & drop a document or click "Choose File"
3. Click "Upload & Generate"
4. View generated flashcards in JSON format

### API Endpoints

**Upload & Generate Flashcards**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@document.pdf" \
  -F "max_q=15" \
  -F "auto_approve=true"
```

**Response Format**
```json
{
  "status": "ok",
  "record_id": "507f1f77bcf86cd799439011",
  "total_flashcards": 12,
  "flashcards": [
    {
      "question": "What are the key principles of photosynthesis?",
      "answer": "Photosynthesis occurs in two stages...",
      "keywords": ["photosynthesis", "chlorophyll", "glucose"],
      "confidence": 0.85
    }
  ]
}
```

### Configuration

**Backend (`backend_flask/config.py`)**
```python
ML_SERVICE_URL = 'http://localhost:8000/generate'  # ML service endpoint
UPLOAD_DIR = './uploads'                            # Upload storage
MONGO_URI = 'mongodb://localhost:27017/'            # MongoDB (optional)
MAX_TOTAL_CHARS = 80000                             # Document size limit
MAX_Q_TOTAL = 25                                    # Max flashcards per document
DEBUG = True                                        # Debug mode
```

**ML Service (`ml_service/config.py`)**
```python
DEFAULT_MODEL_PATH = './model/flashcard_finetuned'  # Fine-tuned model
FALLBACK_MODEL = 't5-small'                         # Fallback model
MAX_INPUT_LENGTH = 512                              # Tokenizer limit
MAX_OUTPUT_LENGTH = 256                             # Generation limit
MAX_KEYWORDS = 5                                    # Keywords per card
```

## 🎯 Advanced Features

### Model Fine-Tuning

Train a custom T5 model on your dataset:

```bash
cd ml_service
python scripts/train_model.py \
  --training_file data/flashcards.jsonl \
  --output_dir model/flashcard_finetuned
```

**Training data format (JSONL)**
```json
{"text": "Photosynthesis is...", "q": "What is photosynthesis?", "a": "Photosynthesis is the process..."}
{"text": "...", "q": "...", "a": "..."}
```

### Environment Variables

```bash
# Backend
export ML_SERVICE_URL=http://ml-service:8000/generate
export MONGO_URI=mongodb://mongo:27017/
export MONGO_DB_NAME=flashcard_db
export UPLOAD_DIR=/data/uploads
export MAX_UPLOAD_SIZE_BYTES=52428800  # 50MB
export DEBUG=False

# ML Service
export PORT=8000
export MAX_QUESTIONS=10
```

### MongoDB Integration (Optional)

Enable database persistence:

```bash
# Start MongoDB
docker run -d -p 27017:27017 mongo:latest

# Set environment variable
export MONGO_URI=mongodb://localhost:27017/

# Restart backend
./run_backend.sh
```

## 📊 Performance

- **Small Documents (< 5 pages)**: ~5-10 seconds
- **Medium Documents (5-20 pages)**: ~15-30 seconds  
- **Large Documents (> 20 pages)**: ~30-60 seconds
- **GPU-Accelerated (CUDA)**: ~3x faster

## 🐛 Troubleshooting

### Models not downloading
```bash
# Manually download models
python ml_service/download_nltk.py
```

### ML Service fails to start
```bash
# Check PyTorch/CUDA compatibility
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

### File extraction errors
```bash
# For scanned PDFs, enable OCR (requires pytesseract + Tesseract):
pip install pytesseract
# Then install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
```

### MongoDB connection issues
```bash
# Verify MongoDB is running
mongosh --version
# Test connection
mongodb://localhost:27017/
```

## 📦 Dependencies

**Backend**
- Flask 2.3.2 - Web framework
- PyMuPDF 1.22.5 - PDF extraction
- python-docx 0.8.11 - DOCX support
- python-pptx 0.6.21 - PPTX support
- pymongo 4.4.0 - Database (optional)
- requests 2.31.0 - HTTP client

**ML Service**
- FastAPI 0.95.2 - API framework
- transformers 4.57.1 - HuggingFace models
- torch 2.9.0 - PyTorch
- keybert 0.7.0 - Keyword extraction
- sentence-transformers 2.2.2 - Embeddings
- nltk 3.9 - NLP utilities

## 🔒 Security Considerations

- ✅ File size limits enforced (50MB default)
- ✅ Allowed file types restricted (.pdf, .docx, .pptx, .txt)
- ✅ Secure filename handling
- ⚠️ Add rate limiting for production (use `flask-limiter`)
- ⚠️ Add authentication before deploying publicly
- ⚠️ Enable HTTPS for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙌 Acknowledgments

- **HuggingFace**: Transformers library and pre-trained models
- **PyMuPDF**: PDF extraction capabilities
- **FastAPI**: Modern async Python framework
- **KeyBERT**: Semantic keyword extraction

## 📞 Support & Contact

For issues, questions, or suggestions:
- Open an GitHub Issue
- Check existing discussions
- Review troubleshooting section above

---

**Built with ❤️ for students and educators worldwide**
