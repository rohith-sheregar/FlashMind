from sqlalchemy import Column, Integer, String
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.services.db_setup import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    
    # Relationship to Decks (One User -> Many Decks)
    decks = relationship("Deck", back_populates="owner")