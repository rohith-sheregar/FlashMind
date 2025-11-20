# FlashMind

A Flashcard generation app using React, FastAPI, and LLMs.

## Setup

### Server
1. `cd server`
2. `python -m venv venv`
3. `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
4. `pip install -r requirements.txt`
5. `uvicorn app.main:app --reload`

### Client
1. `cd client`
2. `npm install`
3. `npm run dev`