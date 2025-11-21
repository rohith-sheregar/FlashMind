from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .card_schema import Card

class DeckBase(BaseModel):
    title: str

class DeckCreate(DeckBase):
    pass

class Deck(DeckBase):
    id: int
    created_at: datetime
    cards: List[Card] = []

    class Config:
        from_attributes = True