from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from app.services.parser_service import ParserService
from app.services.llm_service import LLMService
from app.services.db_setup import SessionLocal
from app.models.deck import Deck
from app.models.flashcard import Flashcard
from app.models.user import User
from app.api.auth import get_current_user
import shutil
import os
import uuid
import json
import asyncio
import time
from typing import Generator

router = APIRouter()

# Temporary storage path
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Store processing status
processing_status = {}

def process_document_task(file_path: str, deck_id: str, filename: str, user_id: int):
    """Enhanced background task with better preprocessing and chunking"""
    print(f"⏳ [Background] Processing {filename} for Deck {deck_id}...")
    
    # Update status
    processing_status[deck_id] = {
        "status": "processing",
        "progress": 0,
        "total_chunks": 0,
        "processed_chunks": 0,
        "cards_generated": 0
    }
    
    db = SessionLocal()
    
    try:
        # 1. Read the file content
        with open(file_path, "rb") as f:
            file_content = f.read()

        processing_status[deck_id]["progress"] = 10

        # 2. Extract and preprocess text
        try:
            text = ParserService.extract_text(file_content, filename)
            print(f"📄 [Background] Text extracted and preprocessed ({len(text)} chars).")
        except Exception as e:
            print(f"⚠️ Parser error: {e}")
            text = file_content.decode('utf-8', errors='ignore')

        if not text.strip():
            print("❌ No text content found")
            processing_status[deck_id]["status"] = "error"
            return

        processing_status[deck_id]["progress"] = 20

        # 3. Smart chunking with overlap
        chunks = ParserService.chunk_text(text, chunk_size=800, overlap=100)
        print(f"🔄 [Background] Created {len(chunks)} optimized chunks")
        
        processing_status[deck_id]["total_chunks"] = len(chunks)
        processing_status[deck_id]["progress"] = 30

        # 4. Create deck first
        new_deck = Deck(title=f"FlashMind: {filename}", user_id=user_id, request_id=deck_id) 
        db.add(new_deck)
        db.commit()
        db.refresh(new_deck)

        # 5. Process chunks with LLM
        llm = LLMService()
        all_cards_data = []

        for i, chunk in enumerate(chunks):
            try:
                print(f"🤖 Processing chunk {i+1}/{len(chunks)}...")
                generated = llm.generate_flashcards(chunk)
                
                # Save cards immediately as they're generated
                for card_data in generated:
                    db_card = Flashcard(
                        deck_id=new_deck.id,
                        user_id=user_id,
                        question=card_data.get('front', 'Unknown Question'),
                        answer=card_data.get('back', 'Unknown Answer')
                    )
                    db.add(db_card)
                    all_cards_data.append(card_data)
                
                db.commit()
                
                # Update progress
                processing_status[deck_id]["processed_chunks"] = i + 1
                processing_status[deck_id]["cards_generated"] = len(all_cards_data)
                processing_status[deck_id]["progress"] = 30 + (60 * (i + 1) / len(chunks))
                
                print(f"   ✅ Chunk {i+1}: Generated {len(generated)} cards (Total: {len(all_cards_data)})")
                
            except Exception as e:
                print(f"   ❌ Error processing chunk {i+1}: {e}")
                continue

        if not all_cards_data:
            print("⚠️ [Background] AI generated no cards.")
            processing_status[deck_id]["status"] = "error"
            return

        processing_status[deck_id]["status"] = "completed"
        processing_status[deck_id]["progress"] = 100
        print(f"✅ [Background] Success! Created Deck ID: {new_deck.id} with {len(all_cards_data)} cards.")

    except Exception as e:
        print(f"❌ [Background Error] {str(e)}")
        processing_status[deck_id]["status"] = "error"
    finally:
        db.close()
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    print(f"➡️ [API] Received upload request: {file.filename}")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.rtf', '.pptx', '.ppt', 
                         '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    try:
        # 1. Save file locally
        file_id = str(uuid.uuid4())
        ext = file.filename.split(".")[-1] if "." in file.filename else "txt"
        # Filename pattern: {user_id}_{timestamp}.pdf
        timestamp = int(time.time())
        safe_filename = f"{current_user.id}_{timestamp}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Generate a tracking ID
        temp_ref_id = str(uuid.uuid4())

        # 3. Initialize processing status
        processing_status[temp_ref_id] = {
            "status": "queued",
            "progress": 0,
            "filename": file.filename
        }

        # 4. Queue the Task
        background_tasks.add_task(process_document_task, file_path, temp_ref_id, file.filename, current_user.id)

        # 5. Return Success
        return {
            "deck_id": temp_ref_id, 
            "message": "File uploaded successfully. Processing started.",
            "filename": file.filename,
            "size": file.size
        }

    except Exception as e:
        print(f"❌ [API Error] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{deck_id}")
async def get_processing_status(deck_id: str, current_user: User = Depends(get_current_user)):
    """Get the processing status of a document"""
    if deck_id not in processing_status:
        raise HTTPException(status_code=404, detail="Processing ID not found")
    
    return processing_status[deck_id]

@router.get("/stream/{deck_id}")
async def stream_flashcards(deck_id: str, current_user: User = Depends(get_current_user)):
    """Stream flashcards and status updates as they are generated."""

    async def event_generator():
        """Async generator that yields flashcards incrementally."""
        last_count = 0
        timeout_count = 0
        max_timeout = 300  # 5 minutes

        while timeout_count < max_timeout:
            status = processing_status.get(deck_id)
            if not status:
                # Unknown processing id
                yield f"data: {json.dumps({'type': 'error', 'message': 'Processing ID not found'})}\n\n"
                break
            
            # Always send latest status
            yield f"data: {json.dumps({'type': 'status', 'data': status})}\n\n"

            db = SessionLocal()
            try:
                deck = db.query(Deck).filter(Deck.request_id == deck_id).first()
                if deck:
                    # Fetch cards in creation order and stream only new ones
                    cards = (
                        db.query(Flashcard)
                        .filter(Flashcard.deck_id == deck.id)
                        .order_by(Flashcard.id.asc())
                        .all()
                    )
                    new_cards = cards[last_count:]
                    for card in new_cards:
                        card_payload = {
                            "type": "card",
                            "data": {
                                "id": str(card.id),
                                "question": card.question,
                                "answer": card.answer,
                            },
                        }
                        yield f"data: {json.dumps(card_payload)}\n\n"

                    last_count = len(cards)
            finally:
                db.close()

            # Stop once processing is marked complete or errored
            if status.get("status") == "completed":
                break
            if status.get("status") == "error":
                yield f"data: {json.dumps({'type': 'error', 'message': 'Processing failed'})}\n\n"
                break

            await asyncio.sleep(2)  # Poll every 2 seconds
            timeout_count += 2

        # Final completion signal for the client
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )