from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from app.services.llm_service import LLMService

router = APIRouter()
llm_service = LLMService()

class QuizRequest(BaseModel):
    cards: List[Dict[str, str]]

@router.post("/generate")
async def generate_quiz(request: QuizRequest):
    try:
        quiz = llm_service.generate_quiz(request.cards)
        if not quiz:
            raise HTTPException(status_code=500, detail="Failed to generate quiz")
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
