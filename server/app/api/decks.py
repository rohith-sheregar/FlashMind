from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.db_setup import get_db
from app.models.deck import Deck

router = APIRouter()

@router.get("/{deck_identifier}")
def get_deck(deck_identifier: str, db: Session = Depends(get_db)):
    # 1. Try to find by Integer ID first (if it's a number)
    if deck_identifier.isdigit():
        deck = db.query(Deck).filter(Deck.id == int(deck_identifier)).first()
    else:
        # 2. Fallback: Find by UUID (request_id)
        deck = db.query(Deck).filter(Deck.request_id == deck_identifier).first()
    
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
        
    # Return the deck with cards
    return {
        "id": deck.id,
        "title": deck.title,
        "cards": [{"front": c.question, "back": c.answer} for c in deck.cards]
    }

@router.get("/")
def get_decks(db: Session = Depends(get_db)):
    # For now, we assume user_id = 1 as per the current auth/seeding logic
    user_id = 1
    decks = db.query(Deck).filter(Deck.user_id == user_id).all()
    
    return [
        {
            "id": deck.id,
            "request_id": deck.request_id,
            "title": deck.title,
            "card_count": len(deck.cards)
        }
        for deck in decks
    ]