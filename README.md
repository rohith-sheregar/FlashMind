# FlashMind - AI Study Companion

> **🚀 Live Demo: [https://flashmind-backend-tvd8.onrender.com/](https://flashmind-backend-tvd8.onrender.com/)**
>
> *(Free tier — first load may take ~30s to wake up. **Note: Check your Spam/Junk folder for the registration OTP verification email!**)*

FlashMind is a premium, AI-powered study platform designed to transform your documents and notes into interactive learning experiences. Simply upload your PDF, DOCX, PPTX, or TXT files, and FlashMind will instantly generate flashcards, summarize key topics, build practice quizzes, and render beautiful visual mind maps.

## Features

- **Document Parsing**: Extract text efficiently from multiple file formats (PDF, DOCX, PPTX, TXT).
- **Smart AI Extraction**: Uses state-of-the-art LLMs (GPT-4o-mini via OpenRouter) to build study materials.
- **Interactive Flashcards**: Includes Text-to-Speech (TTS) integration to read out questions and answers.
- **Dynamic Quizzes**: Test your knowledge with auto-generated multiple-choice questions.
- **Visual Mind Maps**: Render beautiful, interactive Mermaid.js diagrams directly in the browser with Zoom & Pan functionality.
- **Email OTP Verification**: Secure user registration with 6-digit OTP sent via email (check your Spam/Junk folder!).
- **Per-User Document Isolation**: Each user sees only their own uploaded documents.
- **AI Usage Limits**: 5 AI generations per user per day with a visual counter.
- **Premium UI/UX**: Built with a stunning dark theme, CSS glassmorphism, animations, and Lottie vector graphics.

## Tech Stack

- **Backend**: Python, Flask, Flask-JWT-Extended, Flask-Bcrypt, Flask-Limiter
- **Database**: MongoDB (Local or Atlas)
- **Frontend**: Vanilla HTML/CSS/JS with Mermaid.js, Marked.js, and Lottie Player
- **AI Content Generation**: OpenRouter API (GPT-4o-mini)
- **RAG Pipeline**: Local `ml_service` (FastAPI) with SentenceTransformers + Scikit-learn
- **Email Delivery**: EmailJS HTTP REST API (production) / Gmail SMTP (local dev fallback)
- **Deployment**: Render (Web Services) + MongoDB Atlas (Database)

---

## System Architecture & Security

```
                 [ Browser / Client ]
                          │ (HTTPS)
                          ▼
                  [ Render Proxy ]
                          │
                          ▼
            [ Flask Backend (Port 5000) ]
             ├── Auth (JWT & Bcrypt)
             ├── Rate Limiter (Fixed Window)
             ├── Database Client (PyMongo)
             └── Email Handler (EmailJS REST)
               │                      │
       (HTTP)  ▼                      ▼  (HTTPS)
    [ ml_service ]             [ MongoDB Atlas ]
   SentenceTransformers
```

### 1. Embedded Security & Rate Limiting
To prevent abuse, credential stuffing, and resource exhaustion, FlashMind implements an embedded security layer at the application gateway level:
* **Rate Limiting Algorithm (Fixed Window)**: Utilizing `Flask-Limiter` configured with a **Fixed Window** algorithm. Requests are tracked using the client's IP address (`get_remote_address`). If a client exceeds the threshold (default: `10 requests per hour`), the server immediately drops the request with an HTTP `429 Too Many Requests` response.
* **Session Protection**: Stateful sessions are eliminated in favor of stateless JWT tokens (`Flask-JWT-Extended`). Authentication tokens are securely verified on each request, guaranteeing complete backend isolation of user documents and decks.
* **Password Hashing**: Passwords are secure-hashed using `Flask-Bcrypt` (implementing the Blowfish cipher key-derivation function) before entering the database.

### 2. AI & RAG Architecture
FlashMind utilizes a highly optimized **Retrieval-Augmented Generation (RAG)** pipeline to process extremely large documents without exceeding LLM context windows or racking up massive API costs:

1. **Intelligent Chunking**: Large PDFs are broken down into semantically meaningful, overlapping text chunks of `1500` characters, cutting only at sentence endings within a `100` character window. Automatic academic noise and boilerplate (e.g. Table of Contents, copyright notices) are filtered out.
2. **Local Vector Embeddings**: We use HuggingFace's extremely fast `all-MiniLM-L6-v2` SentenceTransformer running on a separate `ml_service` container. This maps each chunk into a 384-dimensional vector space.
3. **K-Means Clustering**: Instead of just sending the first few pages of a document to the LLM, FlashMind runs K-Means clustering on the generated vectors. It selects the most diverse and highly representative chunks across the *entire* document, ensuring all core topics are covered.
4. **Token Efficiency**: By condensing a 500-page book down to its most crucial, diverse embeddings, we pass only the highest quality context to GPT-4o-mini via OpenRouter, resulting in fast, low-cost generations.

---

## Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rohith-sheregar/FlashMind.git
   cd FlashMind
   ```

2. **Setup the Backend**:
   ```bash
   cd backend_flask
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in `backend_flask/` with:
   ```env
   OPENROUTER_API_KEY="your_openrouter_api_key"
   SMTP_EMAIL="your-gmail@gmail.com"
   SMTP_PASSWORD="your-gmail-app-password"
   ```

4. **Run the Application**:
   ```bash
   cd ..
   python -m backend_flask.app
   ```
   Navigate to `http://127.0.0.1:5000` to access the platform.
