# FlashMind - AI Study Companion

FlashMind is a premium, AI-powered study platform designed to transform your documents and notes into interactive learning experiences. Simply upload your PDF, DOCX, PPTX, or TXT files, and FlashMind will instantly generate flashcards, summarize key topics, build practice quizzes, and render beautiful visual mind maps.

## Features

- **Document Parsing**: Extract text efficiently from multiple file formats.
- **Smart AI Extraction**: Uses state-of-the-art LLMs (like OpenAI GPT-4o via OpenRouter) to build study materials.
- **Interactive Flashcards**: Includes Text-to-Speech (TTS) integration to read out questions and answers.
- **Dynamic Quizzes**: Test your knowledge with auto-generated multiple-choice questions.
- **Visual Mind Maps**: Render beautiful, interactive Mermaid.js diagrams directly in the browser with Zoom & Pan functionality.
- **Premium UI/UX**: Built with a stunning dark theme, CSS animations, and Lottie vector graphics for a polished feel.

## Tech Stack

- **Backend**: Python, Flask, Flask-JWT-Extended
- **Database**: MongoDB (Local or Atlas)
- **Frontend**: Vanilla HTML/CSS/JS (no heavy framework required)
- **AI Models**: Local RAG via `ml_service` (HuggingFace transformers) and remote generation via OpenRouter.

## Local Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
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
   Set up your OpenRouter key and MongoDB URI (default is localhost).
   ```bash
   export OPENROUTER_API_KEY="your_api_key_here"
   export MONGO_URI="mongodb://localhost:27017/"
   ```

4. **Run the Application**:
   ```bash
   python -m backend_flask.app
   ```
   Navigate to `http://127.0.0.1:5000` to access the platform.

## Free Deployment Guide

If you want to host FlashMind for free so you and your friends can access it over the internet, you can use **Render** (for the Flask backend) and **MongoDB Atlas** (for the database).

### 1. MongoDB Atlas (Free Database)
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) and create a free account.
2. Create a "Shared Cluster" (M0 Free Tier).
3. Under **Database Access**, create a new user (save the username and password).
4. Under **Network Access**, add `0.0.0.0/0` so your deployed backend can connect to it.
5. Click **Connect**, choose "Connect your application", and copy the connection string (`MONGO_URI`). It will look like: `mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority`.

### 2. Render (Free Web Service)
1. Go to [Render](https://render.com/) and create a free account.
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.
4. Set the following configuration:
   - **Root Directory**: `backend_flask`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn "backend_flask.app:app" -b 0.0.0.0:10000`
5. **Environment Variables**: Add your API keys and MongoDB string:
   - `OPENROUTER_API_KEY`: (Your OpenRouter Key)
   - `MONGO_URI`: (Your MongoDB Atlas connection string)
6. Click **Create Web Service**. 

Render will automatically build and deploy your app. Once finished, you will receive a free `https://your-app-name.onrender.com` link to access your premium FlashMind app!
