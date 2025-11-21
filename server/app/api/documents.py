from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.services.parser_service import ParserService
from app.services.llm_service import LLMService
from app.services.db_setup import SessionLocal
from app.models.deck import Deck
from app.models.flashcard import Flashcard
from app.models.user import User
import shutil
import os
import uuid

# --- CRITICAL FIX: Initialize Router WITHOUT dependencies ---
router = APIRouter() 

# Temporary storage path
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_document_task(file_path: str, deck_id: str, filename: str):
    """
    Background task that runs the actual AI pipeline.
    """
    print(f"⏳ [Background] Processing {filename} for Deck {deck_id}...")
    
    # Create a new DB session for this background thread
    db = SessionLocal()
    
    try:
        # 1. Read the file content
        with open(file_path, "rb") as f:
            file_content = f.read()

        # 2. Extract Text
        # (Ensure ParserService is implemented or mock it for now)
        try:
            text = ParserService.extract_text(file_content, filename)
        except Exception:
            # Fallback if Parser fails (prevent crash)
            text = str(file_content)

        print(f"📄 [Background] Text extracted ({len(text)} chars).")

        # --- FIX 1: Instantiate the Service (Add parenthesis) ---
        llm = LLMService() 

        # --- FIX 2: Chunking Strategy (Critical for T5 Model) ---
        # Split text into 1000-char chunks so the AI doesn't get overwhelmed
        chunk_size = 1000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        all_cards_data = []

        print(f"🔄 [Background] Splitting into {len(chunks)} chunks...")

        for i, chunk in enumerate(chunks):
            # Call the method on the INSTANCE 'llm', not the Class
            generated = llm.generate_flashcards(chunk)
            all_cards_data.extend(generated)
            print(f"   👉 Chunk {i+1}/{len(chunks)}: Generated {len(generated)} cards")

        if not all_cards_data:
            print("⚠️ [Background] AI generated no cards.")
            return

        # 3. Save to SQLite
        # Note: We use the passed deck_id string for the title, but let DB auto-increment the ID
        new_deck = Deck(title=f"Deck: {filename}", user_id=1,request_id=deck_id) 
        db.add(new_deck)
        db.commit()
        db.refresh(new_deck)

        # --- FIX 3: Key Mapping (front/back -> question/answer) ---
        for card in all_cards_data:
            db_card = Flashcard(
                deck_id=new_deck.id,
                question=card.get('front', 'Unknown Question'), # Map 'front' to 'question'
                answer=card.get('back', 'Unknown Answer')       # Map 'back' to 'answer'
            )
            db.add(db_card)
        
        db.commit()
        print(f"✅ [Background] Success! Created Real DB Deck ID: {new_deck.id} with {len(all_cards_data)} cards.")

    except Exception as e:
        print(f"❌ [Background Error] {str(e)}")
    finally:
        # Cleanup
        db.close()
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    print(f"➡️ [API] Received upload request: {file.filename}")
    
    try:
        # 1. Save file locally
        file_id = str(uuid.uuid4())
        ext = file.filename.split(".")[-1] if "." in file.filename else "txt"
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{ext}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Generate a tracking ID
        temp_ref_id = str(uuid.uuid4())

        # 3. Queue the Task
        background_tasks.add_task(process_document_task, file_path, temp_ref_id, file.filename)

        # 4. Return Success
        return {
            "deck_id": temp_ref_id, 
            "message": "File uploaded successfully. Processing started."
        }

    except Exception as e:
        print(f"❌ [API Error] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))