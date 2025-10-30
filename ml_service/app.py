from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn, os, traceback, json, re, logging

# Support running as a package (python -m ml_service.app) and as a script in the ml_service/ folder
try:
    from ml_service.config import PORT, MAX_QUESTIONS
    from ml_service.models.model_manager import ModelManager, ModelLoadError
    from ml_service.models.rule_based import enhanced_rule_based_generate
except ModuleNotFoundError:
    from config import PORT, MAX_QUESTIONS
    from models.model_manager import ModelManager, ModelLoadError
    from models.rule_based import enhanced_rule_based_generate

app = FastAPI(title='Flashcard ML Service (Enhanced)')
logger = logging.getLogger(__name__)


class GenRequest(BaseModel):
    text: str
    max_q: int = 15


# Initialize model manager (may raise if critical libs missing)
MODEL_MANAGER = None
try:
    MODEL_MANAGER = ModelManager()
except ModelLoadError as e:
    logger.warning(f"ModelManager initialization failed: {e}")
    MODEL_MANAGER = None


@app.get('/info')
def info():
    if MODEL_MANAGER:
        return {'model': MODEL_MANAGER.get_model_info()}
    return {'model': {'model_path': None, 'is_fallback': True, 'has_keybert': False}}


@app.post('/generate')
async def generate(req: GenRequest):
    text = (req.text or '').strip()
    max_q = min(req.max_q or 5, MAX_QUESTIONS)
    if not text:
        raise HTTPException(status_code=400, detail='No input text provided')

    # Prefer ML model if available
    try:
        if MODEL_MANAGER:
            try:
                cards = MODEL_MANAGER.generate_flashcards(text, max_q=max_q)
                if cards:
                    return {'flashcards': cards}
            except Exception as e:
                logger.warning(f"Model generation error: {e}")
                traceback.print_exc()

        # Fallback to enhanced rule-based generator
        return {'flashcards': enhanced_rule_based_generate(text, max_q=max_q)}

    except Exception as e:
        logger.error(f"Unexpected error in /generate: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail='Internal server error')


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=PORT)
