"""Rule-based flashcard generation with enhanced features."""
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag

try:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('stopwords')
except Exception:
    print("Warning: NLTK data download failed. Basic tokenization will be used.")

def preprocess_text(text: str) -> list[str]:
    """Split text into clean sentences."""
    try:
        sentences = sent_tokenize(text)
    except Exception:
        # Fallback to basic splitting
        sentences = [s.strip() for s in re.split(r'[.!?]+', text)]
    return [s.strip() for s in sentences if len(s.strip()) > 20]

def extract_definition_sentences(sentences: list[str]) -> list[dict]:
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

def extract_key_terms(text: str, sentence: str) -> list[str]:
    """Extract potential key terms from the sentence."""
    try:
        words = word_tokenize(sentence)
        tagged = pos_tag(words)
        # Focus on nouns and noun phrases
        key_terms = []
        stop_words = set(stopwords.words('english'))
        
        for i, (word, tag) in enumerate(tagged):
            # Get nouns and proper nouns
            if tag.startswith('NN') and word.lower() not in stop_words:
                # Check for compound nouns
                if i > 0 and tagged[i-1][1].startswith('JJ'):
                    key_terms.append(f"{tagged[i-1][0]} {word}")
                else:
                    key_terms.append(word)
        
        return list(set(key_terms))[:5]
    except Exception:
        # Fallback to basic word extraction
        words = re.findall(r'\b\w+\b', sentence)
        return [w for w in words if len(w) > 3][:5]

def enhanced_rule_based_generate(text: str, max_q: int = 5) -> list[dict]:
    """Generate flashcards using enhanced rule-based approach."""
    sentences = preprocess_text(text)
    flashcards = []
    
    # First, look for definition-style sentences
    definitions = extract_definition_sentences(sentences)
    for d in definitions[:max_q]:
        flashcards.append({
            'question': f"What is {d['term']}?",
            'answer': d['definition'],
            'keywords': extract_key_terms(text, d['sentence'])
        })
    
    # If we need more cards, generate from remaining sentences
    remaining = max_q - len(flashcards)
    if remaining > 0:
        # Filter out sentences already used in definitions
        used_sents = set(d['sentence'] for d in definitions)
        other_sents = [s for s in sentences if s not in used_sents]
        
        for sent in other_sents[:remaining]:
            # Try to form a specific question based on sentence structure
            key_terms = extract_key_terms(text, sent)
            if key_terms:
                # Use the first key term to form a question
                main_term = key_terms[0]
                question = f"What is important to know about {main_term}?"
            else:
                # Fallback to generic question
                question = "What is the main idea expressed in this statement?"
            
            flashcards.append({
                'question': question,
                'answer': sent,
                'keywords': key_terms
            })
    
    return flashcards