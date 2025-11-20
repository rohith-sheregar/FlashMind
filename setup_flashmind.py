import os
from pathlib import Path

# Project Name
PROJECT_NAME = "flashmind"

# Base directories
BASE_DIR = Path(PROJECT_NAME)
CLIENT_DIR = BASE_DIR / "client"
SERVER_DIR = BASE_DIR / "server"

# File Contents (Boilerplate)
GITIGNORE_CONTENT = """
# Python
__pycache__/
*.py[cod]
venv/
.env

# Node
node_modules/
dist/
.DS_Store
"""

README_CONTENT = """
# FlashMind

A Flashcard generation app using React, FastAPI, and LLMs.

## Setup

### Server
1. `cd server`
2. `python -m venv venv`
3. `source venv/bin/activate` (Mac/Linux) or `venv\\Scripts\\activate` (Windows)
4. `pip install -r requirements.txt`
5. `uvicorn app.main:app --reload`

### Client
1. `cd client`
2. `npm install`
3. `npm run dev`
"""

REQUIREMENTS_CONTENT = """
fastapi
uvicorn
sqlalchemy
pydantic
python-dotenv
python-multipart
passlib[bcrypt]
python-jose[cryptography]
"""

VITE_CONFIG_CONTENT = """
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    }
  }
})
"""

PACKAGE_JSON_CONTENT = """
{
  "name": "flashmind-client",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "zustand": "^4.4.0",
    "lucide-react": "^0.292.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.2.2",
    "vite": "^5.0.0",
    "tailwindcss": "^3.3.5",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31"
  }
}
"""

FASTAPI_MAIN_CONTENT = """
from fastapi import FastAPI

app = FastAPI(title="FlashMind API")

@app.get("/")
def read_root():
    return {"message": "Welcome to FlashMind API"}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
"""

def create_structure():
    # Define the directory structure
    directories = [
        BASE_DIR,
        # Client Structure
        CLIENT_DIR / "public",
        CLIENT_DIR / "src/components",
        CLIENT_DIR / "src/pages",
        CLIENT_DIR / "src/services",
        CLIENT_DIR / "src/store",
        CLIENT_DIR / "src/types",
        # Server Structure
        SERVER_DIR / "app/api",
        SERVER_DIR / "app/core",
        SERVER_DIR / "app/models",
        SERVER_DIR / "app/schemas",
        SERVER_DIR / "app/services",
    ]

    # Create Directories
    print(f"🚀 Creating project: {PROJECT_NAME}...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   📂 Created: {directory}")

    # Define Files to Create (Path, Content)
    files = [
        # Root
        (BASE_DIR / "README.md", README_CONTENT),
        (BASE_DIR / ".gitignore", GITIGNORE_CONTENT),
        
        # Client Files
        (CLIENT_DIR / "package.json", PACKAGE_JSON_CONTENT),
        (CLIENT_DIR / "vite.config.ts", VITE_CONFIG_CONTENT),
        (CLIENT_DIR / "tsconfig.json", "{}"),
        (CLIENT_DIR / "tailwind.config.js", "export default {\n  content: ['./src/**/*.{js,jsx,ts,tsx}'],\n  theme: { extend: {} },\n  plugins: [],\n}"),
        (CLIENT_DIR / "index.html", "<!DOCTYPE html>\n<html lang='en'>\n<head><title>FlashMind</title></head>\n<body><div id='root'></div><script type='module' src='/src/main.tsx'></script></body>\n</html>"),
        
        # Client Src Files
        (CLIENT_DIR / "src/App.tsx", "function App() { return <div className='p-4 font-bold text-2xl'>FlashMind Client</div> }\nexport default App;"),
        (CLIENT_DIR / "src/main.tsx", "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\nimport './index.css';\n\nReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);"),
        (CLIENT_DIR / "src/index.css", "@tailwind base;\n@tailwind components;\n@tailwind utilities;"),
        
        # Client Placeholders
        (CLIENT_DIR / "src/components/Button.tsx", "// Button Component"),
        (CLIENT_DIR / "src/components/Input.tsx", "// Input Component"),
        (CLIENT_DIR / "src/components/Flashcard.tsx", "// Flashcard Component"),
        (CLIENT_DIR / "src/pages/Landing.tsx", "// Landing Page"),
        (CLIENT_DIR / "src/pages/StudyMode.tsx", "// Study Mode Page"),
        (CLIENT_DIR / "src/services/api.ts", "// Axios setup"),
        
        # Server Files
        (SERVER_DIR / "requirements.txt", REQUIREMENTS_CONTENT),
        (SERVER_DIR / ".env.example", "SECRET_KEY=changeme\nDATABASE_URL=sqlite:///./flashmind.db"),
        (SERVER_DIR / "app/main.py", FASTAPI_MAIN_CONTENT),
        (SERVER_DIR / "app/__init__.py", ""),
        
        # Server Placeholders
        (SERVER_DIR / "app/api/auth.py", "# Auth Routes"),
        (SERVER_DIR / "app/api/documents.py", "# Document Routes"),
        (SERVER_DIR / "app/api/decks.py", "# Deck Routes"),
        (SERVER_DIR / "app/core/config.py", "# App Configuration"),
        (SERVER_DIR / "app/core/security.py", "# Security Utils"),
        (SERVER_DIR / "app/models/user.py", "# User Model"),
        (SERVER_DIR / "app/models/deck.py", "# Deck Model"),
        (SERVER_DIR / "app/models/flashcard.py", "# Flashcard Model"),
        (SERVER_DIR / "app/schemas/deck_schema.py", "# Pydantic Deck Schema"),
        (SERVER_DIR / "app/services/llm_service.py", "# LLM Logic"),
        (SERVER_DIR / "app/services/parser_service.py", "# File Parsing Logic"),
    ]

    # Create Files
    for file_path, content in files:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"   📄 Created: {file_path}")

    print(f"\n✅ {PROJECT_NAME} structure created successfully!")
    print("\nNEXT STEPS:")
    print("1. Run: cd flashmind")
    print("2. Follow the setup instructions in README.md")

if __name__ == "__main__":
    create_structure()