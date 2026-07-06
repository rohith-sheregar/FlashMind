from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn, os, traceback, json, re, logging

# Support running as a package (python -m ml_service.app) and as a script in the ml_service/ folder
try:
    from ml_service.config import PORT
    from ml_service.models.rag_processor import get_rag_processor
except ModuleNotFoundError:
    from config import PORT
    from models.rag_processor import get_rag_processor

app = FastAPI(title='Flashcard ML Service (RAG Only)')
logger = logging.getLogger(__name__)


@app.get('/info')
def info():
    return {'status': 'active', 'rag_model': 'all-MiniLM-L6-v2'}



class RAGRequest(BaseModel):
    text: str
    max_output_chars: int = 15000

@app.post('/api/rag/condense')
async def rag_condense(req: RAGRequest):
    text = (req.text or '').strip()
    if not text:
        raise HTTPException(status_code=400, detail='No input text provided')
        
    try:
        rag = get_rag_processor()
        condensed = rag.condense_text(text, max_output_chars=req.max_output_chars)
        return {'condensed_text': condensed}
    except Exception as e:
        logger.error(f"Error in /api/rag/condense: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail='Internal server error')


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=PORT)
