"""
Flashcard generation pipeline for educational notes.

- Cleans input text (removes page numbers, headers, 'Lecture Notes', empty lines)
- Splits text into meaning-based chunks (definitions, objectives, advantages, etc.)
- For each chunk, calls the fine-tuned model with a prompt for exam-style Q&A
- Parses model output into structured JSON: {"question": ..., "answer": ..., "keywords": [...]}
- Falls back to rule-based generator if model output fails
- Extracts 3–5 keywords using KeyBERT or Sentence-Transformers
- Returns a list of flashcards as JSON

Usage:
    from ml_service.scripts.flashcard_pipeline import generate_flashcards_from_text
    flashcards = generate_flashcards_from_text(raw_text)
"""
import re
import logging
from typing import List, Dict
from ml_service.models.model_manager import ModelManager
from ml_service.models.rule_based import enhanced_rule_based_generate

logger = logging.getLogger(__name__)

HEADER_PATTERNS = [
    r"^\s*Page \d+\s*$",
    r"^Lecture Notes.*$",
    r"^\s*\d+\s*$",
    r"^\s*Slide \d+\s*$",
]

SECTION_SPLIT_PATTERNS = [
    r"\bdefinitions?\b",
    r"\bobjectives?\b",
    r"\badvantages?\b",
    r"\bdisadvantages?\b",
    r"\btypes?\b",
    r"\bimportance\b",
    r"\bapplications?\b",
    r"\bexamples?\b",
    r"\bconclusion\b",
]


def clean_text(text: str) -> str:
    """Remove headers, page numbers, and empty lines."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        skip = False
        for pat in HEADER_PATTERNS:
            if re.match(pat, line, re.IGNORECASE):
                skip = True
                break
        if not skip:
            cleaned.append(line)
    return "\n".join(cleaned)


def split_into_chunks(text: str) -> List[str]:
    """Split text into meaning-based chunks using section headers and heuristics."""
    # Split on section headers
    pattern = re.compile(r"(^|\n)(?P<header>(%s))[:\n]" % "|".join(SECTION_SPLIT_PATTERNS), re.IGNORECASE)
    splits = [m.start() for m in pattern.finditer(text)]
    if not splits:
        # fallback: split by paragraphs
        paras = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 40]
        return paras
    chunks = []
    for i, start in enumerate(splits):
        end = splits[i+1] if i+1 < len(splits) else len(text)
        chunk = text[start:end].strip()
        if len(chunk) > 40:
            chunks.append(chunk)
    return chunks


def generate_flashcards_from_text(text: str, max_q_per_chunk: int = 2) -> List[Dict]:
    """Main pipeline: clean, chunk, generate, parse, extract keywords."""
    model_mgr = ModelManager()
    cleaned = clean_text(text)
    chunks = split_into_chunks(cleaned)
    flashcards = []
    for chunk in chunks:
        prompt = f"Generate an exam-style question (5–9 marks) and answer from this content: {chunk}"
        try:
            # Try model-based generation
            outputs = model_mgr.pipeline(
                prompt,
                max_length=256,
                min_length=50,
                num_beams=2,
                temperature=0.7,
                do_sample=True
            )
            output_text = outputs[0]['generated_text']
            # Try to parse output as JSON
            card = None
            try:
                import json
                card = json.loads(output_text)
                if isinstance(card, dict) and 'question' in card and 'answer' in card:
                    pass
                elif isinstance(card, list) and card and 'question' in card[0]:
                    card = card[0]
                else:
                    raise ValueError('Model output not in expected format')
            except Exception:
                # Try to extract Q/A with regex
                q_match = re.search(r'question\s*[:\-]\s*(.+)', output_text, re.I)
                a_match = re.search(r'answer\s*[:\-]\s*(.+)', output_text, re.I)
                if q_match and a_match:
                    card = {
                        'question': q_match.group(1).strip(),
                        'answer': a_match.group(1).strip()
                    }
            if not card:
                raise ValueError('Could not parse model output')
            # Extract keywords
            card['keywords'] = model_mgr._extract_keywords(card['answer'], top_n=5)
            flashcards.append(card)
        except Exception as e:
            logger.warning(f"Model failed for chunk, using rule-based: {e}")
            # Fallback to rule-based
            for card in enhanced_rule_based_generate(chunk, max_q=max_q_per_chunk):
                if 'keywords' not in card or not card['keywords']:
                    card['keywords'] = model_mgr._extract_keywords(card['answer'], top_n=5)
                flashcards.append(card)
    return flashcards
