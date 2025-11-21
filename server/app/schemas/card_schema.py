from pydantic import BaseModel

class CardBase(BaseModel):
    question: str
    answer: str

class CardCreate(CardBase):
    pass

class Card(CardBase):
    id: int
    deck_id: int

    class Config:
        from_attributes = True