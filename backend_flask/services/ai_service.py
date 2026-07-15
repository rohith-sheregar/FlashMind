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

MIN_FLASHCARDS = 20
MAX_FLASHCARDS = 50
MIN_QUIZ_QUESTIONS = 20
MAX_QUIZ_QUESTIONS = 35


def _word_count(text: str) -> int:
    return len((text or "").split())


def _target_flashcard_count(text: str, requested_max: int = None) -> int:
    if requested_max:
        return max(1, min(int(requested_max), MAX_FLASHCARDS))

    words = _word_count(text)
    if words < 1200:
        return MIN_FLASHCARDS
    if words < 3000:
        return 30
    if words < 7000:
        return 40
    return MAX_FLASHCARDS


def _target_quiz_count(text: str) -> int:
    words = _word_count(text)
    if words < 2500:
        return MIN_QUIZ_QUESTIONS
    if words < 7000:
        return 25
    return MAX_QUIZ_QUESTIONS


def _target_topic_words(text: str) -> int:
    words = _word_count(text)
    if words < 1200:
        return 200
    if words < 3500:
        return 280
    if words < 9000:
        return 350
    return 400


def get_document_text(filepath) -> str:
    """Extract text from the given file using the existing file_service."""
    try:
        from backend_flask.services import file_service
    except ModuleNotFoundError:
        import services.file_service as file_service

    if isinstance(filepath, (list, tuple)):
        parts = []
        for idx, single_path in enumerate(filepath, start=1):
            extracted = get_document_text(single_path)
            if extracted:
                parts.append(f"Source {idx}: {single_path}\n{extracted}")
        return "\n\n".join(parts)

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
        resp = requests.post(url, json={"text": text, "max_output_chars": max_output_chars}, timeout=300)
        resp.raise_for_status()
        return resp.json().get('condensed_text', text[:max_output_chars])
    except Exception as e:
        logger.warning(f"RAG condensation failed, falling back to truncation: {e}")
        return text[:max_output_chars]

def call_openrouter(system_prompt: str, user_prompt: str, max_tokens: int = None) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured.")
        
    try:
        kwargs = {}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            **kwargs,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenRouter API call failed: {e}")
        raise

def generate_quiz(text: str) -> list:
    question_count = _target_quiz_count(text)
    system_prompt = (
        "You are an expert educator. Based on the provided document text, "
        f"generate exactly {question_count} multiple-choice quiz questions testing the most important concepts. "
        "For very short documents, still produce 20 useful questions by varying recall, application, and reasoning questions without inventing facts. "
        "IMPORTANT: STRICTLY IGNORE any administrative boilerplate such as Vision, Mission, Program Outcomes, Course Objectives, Table of Contents, or College information. Focus ONLY on the educational subject matter.\n"
        "Respond ONLY with a valid JSON array of objects, where each object has: "
        "'question' (str), 'options' (list of 4 str), 'correct_index' (int 0-3), and 'explanation' (str)."
    )
    
    rag_text = _get_rag_context(text, max_output_chars=26000)
    response_text = call_openrouter(system_prompt, f"Document Text:\n{rag_text}", max_tokens=10000)
    
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
        "2. The root node must be on the next line, indented by 2 spaces (e.g., `  root((📚 Subject Title))`)\n"
        "3. ALL subsequent branches MUST be created using ONLY indentation (spaces). DO NOT USE ARROWS (`-->` or `-.->`).\n"
        "4. Example syntax:\n"
        "mindmap\n"
        "  root((Root Node))\n"
        "    Branch 1\n"
        "      Sub-branch 1\n"
        "    Branch 2\n"
        "5. Keep node text extremely concise but highly descriptive (2-5 words max).\n"
        "6. Include relevant emojis in nodes to make it visually memorable.\n"
        "7. Do NOT include any markdown wrappers like ```mermaid in your output, just the raw code.\n"
        "8. STRICTLY IGNORE administrative boilerplate (Vision, Mission, Program Outcomes, Index). Focus ONLY on subject matter.\n"
    )
    rag_text = _get_rag_context(text)
    
    response_text = call_openrouter(system_prompt, f"Document Text:\n{rag_text}")
    
    if "```mermaid" in response_text:
        response_text = response_text.split("```mermaid")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
        
    return response_text

def extract_topics(text: str) -> str:
    target_words = _target_topic_words(text)
    system_prompt = (
        "You are an expert at summarizing documents. Based on the provided document text, "
        "extract the most important concepts/topics. "
        f"Write about {target_words} words total, scaling detail to the document size. "
        "IMPORTANT: STRICTLY IGNORE any administrative boilerplate such as Vision, Mission, Program Outcomes, Course Objectives, Table of Contents, or College information. Focus ONLY on the educational subject matter.\n"
        "Return polished Markdown with clear section headings, concise bullets, bolded key terms, and short explanations."
    )
    rag_text = _get_rag_context(text, max_output_chars=26000)
    return call_openrouter(system_prompt, f"Document Text:\n{rag_text}", max_tokens=2500)

def generate_flashcards(text: str, max_q: int = None) -> list:
    """Generate high-quality, deep-concept flashcards using OpenRouter."""
    target_count = _target_flashcard_count(text, max_q)
    system_prompt = (
        "You are an expert cognitive psychologist and educator. Based on the provided document text, "
        f"create exactly {target_count} highly significant flashcards covering the strongest concepts, mechanisms, or principles. "
        "CRITICAL INSTRUCTIONS: "
        "- Do NOT ask trivial or surface-level questions (e.g., 'What is the title of the document?', 'What is important to know about X?'). "
        "- Focus on 'Why' and 'How' questions that test deep comprehension. "
        "- Keep answers concise but complete enough for revision. "
        "- STRICTLY IGNORE any administrative boilerplate (Vision, Mission, Program Outcomes, Index, College names). Focus ONLY on educational material. "
        "- Format your response ONLY as a valid JSON array of objects, where each object has: "
        "'question' (string) and 'answer' (string)."
    )
    # Using gpt-4o for highest quality extraction
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured.")
        
    try:
        rag_text = _get_rag_context(text, max_output_chars=30000)
        
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Document Text:\n{rag_text}"},
            ],
            temperature=0.4,
            max_tokens=12000,
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
