import os
import json
import logging
import requests
from openai import OpenAI

try:
    from backend_flask.config import OPENROUTER_API_KEY
except ModuleNotFoundError:
    from config import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)

# Initialize OpenAI client pointed to OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY or "DUMMY_KEY",
)

def get_document_text(filepath: str) -> str:
    """Extract text from the given file using the existing file_service."""
    try:
        from backend_flask.services import file_service
    except ModuleNotFoundError:
        import services.file_service as file_service
        
    try:
        chunks = file_service.extract_text_chunks(filepath, max_chunk_chars=4000, overlap_chars=0)
        return "\n\n".join(chunk.get("text", "") for chunk in chunks)
    except Exception as e:
        logger.error(f"Failed to extract text from {filepath}: {e}")
        return ""

def _get_rag_context(text: str, max_output_chars: int = 15000) -> str:
    """Pass text to ml_service RAG condensation endpoint."""
    try:
        from backend_flask.config import ML_SERVICE_URL
    except ModuleNotFoundError:
        try:
            from config import ML_SERVICE_URL
        except ModuleNotFoundError:
            ML_SERVICE_URL = "http://localhost:8000"
            
    try:
        # If the environment variable accidentally included /generate from the old setup, remove it.
        base_url = ML_SERVICE_URL.split('/generate')[0].rstrip('/')
        url = f"{base_url}/api/rag/condense"
        resp = requests.post(url, json={"text": text, "max_output_chars": max_output_chars}, timeout=30)
        resp.raise_for_status()
        return resp.json().get('condensed_text', text[:max_output_chars])
    except Exception as e:
        logger.warning(f"RAG condensation failed, falling back to truncation: {e}")
        return text[:max_output_chars]

def call_openrouter(system_prompt: str, user_prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured.")
        
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenRouter API call failed: {e}")
        raise

def generate_quiz(text: str) -> list:
    system_prompt = (
        "You are an expert educator. Based on the provided document text, "
        "generate a 5-question multiple-choice quiz testing the most important concepts. "
        "Respond ONLY with a valid JSON array of objects, where each object has: "
        "'question' (str), 'options' (list of 4 str), 'correct_index' (int 0-3), and 'explanation' (str)."
    )
    
    rag_text = _get_rag_context(text)
    response_text = call_openrouter(system_prompt, f"Document Text:\n{rag_text}")
    
    # Try to parse JSON from the response (sometimes it wraps in markdown code blocks)
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse quiz JSON: {e}\nResponse: {response_text}")
        raise ValueError("Failed to generate valid quiz format.")

def generate_mindmap(text: str) -> str:
    system_prompt = (
        "You are an expert educator and visual designer. Based on the provided document text, "
        "create a highly detailed and memorable Mermaid.js mindmap summarizing the key concepts. "
        "CRITICAL INSTRUCTIONS:\n"
        "1. Start your response with exactly: `mindmap` on the first line.\n"
        "2. The root node should clearly summarize the document's main subject and be centered. Use emojis for context (e.g., `root((📚 Subject Title))`)\n"
        "3. Create at least 3-5 primary branches. Use distinct shapes for different hierarchical levels (e.g., `[Branch]`, `(Sub-branch)`, `((Detail))`).\n"
        "4. Keep node text extremely concise but highly descriptive (2-5 words max).\n"
        "5. Include relevant emojis or icons in many nodes to make it visually memorable and easier to study.\n"
        "6. Do NOT include any markdown wrappers like ```mermaid in your output, just the raw code.\n"
    )
    rag_text = _get_rag_context(text)
    
    response_text = call_openrouter(system_prompt, f"Document Text:\n{rag_text}")
    
    if "```mermaid" in response_text:
        response_text = response_text.split("```mermaid")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
        
    return response_text

def extract_topics(text: str) -> str:
    system_prompt = (
        "You are an expert at summarizing documents. Based on the provided document text, "
        "extract the 5-7 most important concepts/topics. "
        "Return the response formatted beautifully as a Markdown list with a brief 1-sentence description for each."
    )
    rag_text = _get_rag_context(text)
    return call_openrouter(system_prompt, f"Document Text:\n{rag_text}")

def generate_flashcards(text: str, max_q: int = 15) -> list:
    """Generate high-quality, deep-concept flashcards using OpenRouter."""
    system_prompt = (
        "You are an expert cognitive psychologist and educator. Based on the provided document text, "
        f"extract up to {max_q} highly significant concepts, mechanisms, or principles, and convert them into flashcards. "
        "CRITICAL INSTRUCTIONS: "
        "- Do NOT ask trivial or surface-level questions (e.g., 'What is the title of the document?', 'What is important to know about X?'). "
        "- Focus on 'Why' and 'How' questions that test deep comprehension. "
        "- Format your response ONLY as a valid JSON array of objects, where each object has: "
        "'question' (string) and 'answer' (string)."
    )
    # Using gpt-4o for highest quality extraction
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured.")
        
    try:
        rag_text = _get_rag_context(text, max_output_chars=20000)
        
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Document Text:\n{rag_text}"},
            ],
            temperature=0.4,
            max_tokens=2000,
        )
        response_text = response.choices[0].message.content
        
        # Parse JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Failed to generate flashcards: {e}")
        return []
