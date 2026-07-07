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
- **Email Delivery**: Resend HTTP API (production) / Gmail SMTP (local dev)
- **Deployment**: Render (Web Services) + MongoDB Atlas (Database)

## AI & RAG Architecture

FlashMind utilizes a highly optimized **Retrieval-Augmented Generation (RAG)** pipeline to process extremely large documents without exceeding LLM context windows or racking up massive API costs:

1. **Intelligent Chunking**: Large PDFs are broken down into semantically meaningful, overlapping text chunks (preserving sentence boundaries) with automatic boilerplate filtering (removes Vision/Mission statements, Table of Contents, etc.).
2. **Local Embeddings**: We use HuggingFace's extremely fast `all-MiniLM-L6-v2` SentenceTransformer running on a separate `ml_service`. This guarantees zero latency for vector generation.
3. **K-Means Clustering**: Instead of just sending the first few pages to an LLM, FlashMind uses K-Means clustering on the generated embeddings. It selects the most diverse and highly representative chunks across the *entire* document, ensuring all core topics are covered.
4. **Token Efficiency**: By condensing a large document down to its most crucial, diverse embeddings, we pass only the highest quality data to GPT-4o-mini via OpenRouter, resulting in faster generation and incredibly deep, comprehensive study materials.

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

## Free Deployment Guide

Host FlashMind for free using **Render** (web services) and **MongoDB Atlas** (database).

### 1. MongoDB Atlas (Free Database)
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) and create a free account.
2. Create a "Shared Cluster" (M0 Free Tier).
3. Under **Database Access**, create a new user (save the username and password).
4. Under **Network Access**, add `0.0.0.0/0` so your deployed backend can connect.
5. Click **Connect** → **Drivers** → copy the connection string (`MONGO_URI`).

### 2. Resend (Free Email API)
1. Go to [Resend](https://resend.com) and create a free account.
2. Go to **API Keys** and generate a new key.
3. Copy the API key — you will add it as an environment variable on Render.

### 3. Render (Free Web Service)
1. Go to [Render](https://render.com/) and create a free account.
2. Deploy the **Backend**: Click **New +** → **Web Service** → connect your GitHub repo.
   - **Root Directory**: `backend_flask`
   - **Environment**: `Docker`
   - **Instance Type**: `Free`
3. Add **Environment Variables**:
   - `MONGO_URI`: Your MongoDB Atlas connection string
   - `MONGO_DB_NAME`: `flashcard_db`
   - `OPENROUTER_API_KEY`: Your OpenRouter API key
   - `JWT_SECRET_KEY`: A secure random string
   - `RESEND_API_KEY`: Your Resend API key
4. Click **Deploy**. Once live, you'll receive a free `https://your-app.onrender.com` URL!
