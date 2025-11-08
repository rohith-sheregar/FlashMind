"""Rule-based flashcard generation with enhanced features.

This module avoids heavy NLTK top-level imports so that importing the
package doesn't attempt to download or access nltk data (which can cause
LookupError on systems without the corpora). Imports are performed lazily
inside functions and fall back to simple heuristics when NLTK isn't
available or data is missing.
"""
import re
from typing import List, Dict


def _safe_sent_tokenize(text: str) -> List[str]:
    try:
        from nltk.tokenize import sent_tokenize
        return sent_tokenize(text)
    except Exception:
        # Fallback basic sentence splitter
        return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]


def _safe_word_tokenize(sentence: str) -> List[str]:
    try:
        from nltk.tokenize import word_tokenize
        return word_tokenize(sentence)
    except Exception:
        return re.findall(r"\b\w+\b", sentence)


def _safe_pos_tag(words: List[str]):
    try:
        from nltk import pos_tag
        return pos_tag(words)
    except Exception:
        # Return naive noun tagging: mark words longer than 2 chars as nouns
        return [(w, 'NN') for w in words]


def _safe_stopwords_set():
    try:
        from nltk.corpus import stopwords
        return set(stopwords.words('english'))
    except Exception:
        return set()


def preprocess_text(text: str) -> List[str]:
    """Split text into clean sentences."""
    sentences = _safe_sent_tokenize(text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def extract_definition_sentences(sentences: List[str]) -> List[Dict]:
    """Identify sentences that contain definitions or key concepts."""
    definition_patterns = [
        r'\bis\s+(?:defined\s+as|called|known\s+as)\b',
        r'\bmeans\b',
        r'\brefers\s+to\b',
        r'\bconsists\s+of\b'
    ]
    definitions = []
    for sent in sentences:
        for pattern in definition_patterns:
            if re.search(pattern, sent, re.I):
                parts = re.split(pattern, sent, maxsplit=1, flags=re.I)
                if len(parts) == 2:
                    term = parts[0].strip()
                    definition = parts[1].strip()
                    definitions.append({
                        'term': term,
                        'definition': definition,
                        'sentence': sent
                    })
                break
    return definitions


def extract_key_terms(text: str, sentence: str) -> List[str]:
    """Extract potential key terms from the sentence."""
    try:
        words = _safe_word_tokenize(sentence)
        tagged = _safe_pos_tag(words)
        key_terms = []
        stop_words = _safe_stopwords_set()

        for i, (word, tag) in enumerate(tagged):
            if tag.startswith('NN') and word.lower() not in stop_words:
                if i > 0 and tagged[i-1][1].startswith('JJ'):
                    key_terms.append(f"{tagged[i-1][0]} {word}")
                else:
                    key_terms.append(word)

        return list(dict.fromkeys(key_terms))[:5]
    except Exception:
        words = re.findall(r"\b\w+\b", sentence)
        return [w for w in words if len(w) > 3][:5]


def enhanced_rule_based_generate(text: str, max_q: int = 5) -> List[Dict]:
    """Generate flashcards using enhanced rule-based approach."""
    sentences = preprocess_text(text)
    flashcards: List[Dict] = []

    definitions = extract_definition_sentences(sentences)
    for d in definitions[:max_q]:
        flashcards.append({
            'question': f"What is {d['term']}?",
            'answer': d['definition'],
            'keywords': extract_key_terms(text, d['sentence'])
        })

    remaining = max_q - len(flashcards)
    if remaining > 0:
        used_sents = set(d['sentence'] for d in definitions)
        other_sents = [s for s in sentences if s not in used_sents]

        for sent in other_sents[:remaining]:
            key_terms = extract_key_terms(text, sent)
            if key_terms:
                main_term = key_terms[0]
                question = f"What is important to know about {main_term}?"
            else:
                question = "What is the main idea expressed in this statement?"

            flashcards.append({
                'question': question,
                'answer': sent,
                'keywords': key_terms
            })

    return flashcards