from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import documents, decks, auth
from app.services.db_setup import engine, Base, SessionLocal  # <--- Fixed Import
from app.models import user, deck, flashcard
from app.models.user import User  # <--- Fixed Import for seeding

# 1. Create Database Tables
Base.metadata.create_all(bind=engine)

# 2. Seed Test User (Crucial for Foreign Key checks)
try:
    db = SessionLocal()
    # Check if User 1 exists
    user_exists = db.query(User).filter(User.id == 1).first()
    if not user_exists:
        print("👤 Creating Test User (ID: 1)...")
        test_user = User(id=1, email="test@flashmind.com", password_hash="dev_mode_password")
        db.add(test_user)
        db.commit()
        print("✅ Test User Created Successfully.")
    else:
        print("👤 Test User (ID: 1) already exists.")
    db.close()
except Exception as e:
    print(f"⚠️ Warning during user seeding: {e}")

# 3. Initialize App
app = FastAPI(title="FlashMind API")

# 4. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Mount Routers
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(decks.router, prefix="/api/decks", tags=["Decks"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])

@app.get("/")
def root():
    return {"status": "FlashMind API is running"}