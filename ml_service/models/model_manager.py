"""Model management and loading utilities."""
import json
import logging
import re
from pathlib import Path
from typing import Optional, Dict, List, Any

import torch
try:
    from ml_service.config import DEFAULT_MODEL_PATH, FALLBACK_MODEL, MAX_INPUT_LENGTH, MAX_OUTPUT_LENGTH
    from ml_service.models.rule_based import enhanced_rule_based_generate
except ModuleNotFoundError:
    from config import DEFAULT_MODEL_PATH, FALLBACK_MODEL, MAX_INPUT_LENGTH, MAX_OUTPUT_LENGTH
    from models.rule_based import enhanced_rule_based_generate

logger = logging.getLogger(__name__)

class ModelLoadError(Exception):
    """Raised when model loading fails."""
    pass

class ModelNotFoundError(Exception):
    """Raised when model file is not found."""
    pass

class ModelManager:
    """Manager for seq2seq flashcard generation.

    Methods always return sanitized lists (never raw strings). On failures,
    methods return an empty list or the rule-based fallback.
    """
    def __init__(self,
                 model_dir: Optional[str] = None,
                 device: Optional[str] = None,
                 tokenizer_name: Optional[str] = None):
        """Initialize ModelManager.

        Args:
            model_dir: path to fine-tuned model directory. If None, use DEFAULT_MODEL_PATH or FALLBACK_MODEL.
            device: 'cuda' or 'cpu'. Auto-detects via torch.cuda.is_available() if None.
            tokenizer_name: override tokenizer name.
        """
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_dir = model_dir or (DEFAULT_MODEL_PATH if Path(DEFAULT_MODEL_PATH).exists() else FALLBACK_MODEL)
        self.tokenizer_name = tokenizer_name
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForSeq2SeqLM] = None
        self._load_models()

        # Try to load KeyBERT backend; optional
        self._kw_model = None
        try:
            from keybert import KeyBERT
            from sentence_transformers import SentenceTransformer
            sbert = SentenceTransformer('all-MiniLM-L6-v2')
            self._kw_model = KeyBERT(sbert)
            logger.info("KeyBERT available for keyword extraction")
        except Exception:
            self._kw_model = None

    def _load_models(self) -> None:
        """Load tokenizer and model to device; fall back to lightweight defaults if needed."""
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        model_name = self.model_dir
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name or model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval() # Set to evaluation mode
            logger.info("Loaded model %s on device %s", model_name, self.device)
        except Exception as e:
            logger.exception("Failed to load model/tokenizer: %s", e)
            # Ensure attributes are None on failure
            self.model = None
            self.tokenizer = None

    def generate_flashcards(self,
                           text: str,
                           max_q: int = 10,
                           max_length: int = 512,
                           temperature: float = 0.0,
                           do_sample: bool = False) -> List[dict]:
        """
        Generate flashcards from input text using the seq2seq model.

        Returns a list of dicts: {question, answer, keywords}.
        On any error or parse failure, returns rule-based fallback list.
        """
        if not text or not text.strip():
            return []

        if not self.model or not self.tokenizer:
            logger.warning("Model or tokenizer not loaded; using fallback rule-based generator")
            return self.fallback_rule_based(text, max_q)

        prompt = f"""From the text below, generate up to {max_q} detailed, exam-style questions suitable for 5 to 9 marks. For each question, provide a comprehensive answer that would be sufficient for earning full marks.
Return the output as a valid JSON array of objects, where each object has a "question" and an "answer" key.

Text: {text}
"""

        try:
            inputs = self.tokenizer([prompt], return_tensors='pt', truncation=True, padding='max_length', max_length=MAX_INPUT_LENGTH).to(self.device)
            with torch.no_grad():
                gen = self.model.generate(**inputs,
                                          max_length=max_length,
                                          do_sample=do_sample,
                                          temperature=temperature,
                                          num_beams=2)
            decoded = self.tokenizer.batch_decode(gen, skip_special_tokens=True)
            raw_out = decoded[0] if decoded else ""

            # Safety checks
            if not raw_out or len(raw_out) > 20000 or re.fullmatch(r"\d+", raw_out.strip()):
                logger.warning("Model output suspicious; falling back. len=%s", len(raw_out))
                return self.fallback_rule_based(text, max_q)

            parsed = self.parse_model_output(raw_out, max_q)
            if not parsed:
                logger.info("Parsed zero flashcards from model output; using fallback")
                return self.fallback_rule_based(text, max_q)

            validated = self.validate_flashcards(parsed)
            if not validated:
                logger.info("No valid flashcards after validation; using fallback")
                return self.fallback_rule_based(text, max_q)

            # Enrich with keywords
            for fc in validated:
                if self._kw_model:
                    try:
                        kws = self._kw_model.extract_keywords(fc['answer'], top_n=5, keyphrase_ngram_range=(1, 2), stop_words='english')
                        fc['keywords'] = [k[0] for k in kws if len(k[0]) >= 3]
                    except Exception:
                        fc['keywords'] = self._simple_keyword_extract(fc['answer'], top_n=5)
                else:
                    fc['keywords'] = self._simple_keyword_extract(fc['answer'], top_n=5)

            return validated

        except Exception as e:
            logger.exception("Model generation failed: %s", e)
            return self.fallback_rule_based(text, max_q)

    def parse_model_output(self, raw: str, max_q: int) -> List[dict]:
        """
        Robust parser for model-generated text. Attempts JSON parsing first, then
        falls back to line-based Q/A parsing and heuristics.
        """
        if not raw or not raw.strip():
            return []

        # sanitize common artifacts
        s = raw.replace('\r', '\n')
        s = re.sub(r"see above", "", s, flags=re.I)
        s = re.sub(r"page\s+\d+", "", s, flags=re.I)

        # Try full JSON
        try: # Direct JSON load
            obj = json.loads(s)
            if isinstance(obj, list):
                out = []
                for item in obj[:max_q]:
                    if isinstance(item, dict):
                        q = str(item.get('question', '')).strip()
                        a = str(item.get('answer', '')).strip()
                        out.append({'question': q, 'answer': a})
                return out
        except Exception:
            pass

        # Try safe JSON extract
        obj = self._safe_json_extract(s)
        if obj and isinstance(obj, list):
            out = []
            for item in obj[:max_q]:
                if isinstance(item, dict):
                    q = str(item.get('question', '')).strip()
                    a = str(item.get('answer', '')).strip()
                    out.append({'question': q, 'answer': a})
            if out:
                return out

        # Try Q/A line parsing
        qa = self._parse_qa_lines(s)
        if qa:
            return qa[:max_q]

        # Try numbered/bullet list heuristics: split by blank lines and pair sequentially
        parts = [p.strip() for p in re.split(r'\n{1,}', s) if p.strip()]
        candidates: List[Dict[str, str]] = []
        i = 0
        while i < len(parts) - 1 and len(candidates) < max_q:
            p1 = parts[i]
            p2 = parts[i + 1]
            # if p1 ends with '?' treat as question
            if p1.endswith('?'):
                candidates.append({'question': p1, 'answer': p2})
                i += 2
            else:
                # if p1 short and p2 longer, use as Q/A
                if len(p1) < 120 and len(p2) > len(p1):
                    candidates.append({'question': p1, 'answer': p2})
                    i += 2
                else:
                    i += 1
        if candidates:
            return candidates[:max_q]

        # Nothing parsed
        return []

    def validate_flashcards(self, fcs: List[dict]) -> List[dict]:
        """
        Validate and sanitize flashcards. Adds 'confidence' score and ensures
        required keys. Removes duplicates and truncates long answers.
        """
        seen = set()
        out: List[dict] = []
        for item in fcs:
            q = str(item.get('question', '')).strip() if item.get('question') else ''
            a = str(item.get('answer', '')).strip() if item.get('answer') else ''
            if not q or not a:
                continue
            # sanitize
            q = re.sub(r'\s+', ' ', q)
            a = re.sub(r'\s+', ' ', a)
            # remove short page markers
            a = re.sub(r'page\s+\d+', '', a, flags=re.I)
            # truncate
            if len(a) > 4000:
                a = a[:4000]
            key = (q.lower(), a.lower())
            if key in seen:
                continue
            seen.add(key)
            # simple confidence scoring
            conf = self._score_confidence(q, a, item.get('keywords', []))
            out.append({'question': q, 'answer': a, 'keywords': item.get('keywords', []), 'confidence': conf})
        return out

    def _score_confidence(self, q: str, a: str, keywords: Optional[List[str]] = None) -> float:
        """Heuristic confidence scoring.

        - base 0.5
        - +0.2 if keywords present
        - +0.2 if answer length in [50,800]
        - -0.1 if question is simple definition (starts with 'What is')
        - clamp to [0.0,1.0]
        """
        score = 0.5
        kws = keywords or []
        if kws:
            score += 0.2
        if 50 <= len(a) <= 800:
            score += 0.2
        if re.match(r'^what is\b', q.lower()):
            score -= 0.1
        else:
            score += 0.05
        return max(0.0, min(1.0, round(score, 3)))

    def fallback_rule_based(self, text: str, max_q: int) -> List[dict]:
        """Return flashcards from the rule-based generator."""
        try:
            res = enhanced_rule_based_generate(text, max_q)
            # ensure normalized schema
            normalized = []
            for r in res:
                q = r.get('question', '').strip()
                a = r.get('answer', '').strip()
                kws = r.get('keywords', []) if isinstance(r.get('keywords', []), list) else []
                normalized.append({'question': q, 'answer': a, 'keywords': kws, 'confidence': 0.5})
            return normalized
        except Exception as e:
            logger.exception("Rule-based fallback failed: %s", e)
            return []

    def get_model_info(self) -> Dict[str, Any]:
        return {
            'model_path': self.model_dir,
            'is_fallback': self.model is None,
            'has_keybert': self._kw_model is not None
        }

    def _safe_json_extract(self, s: str) -> Optional[Any]:
        """Try to extract a JSON object/array from a string. Returns Python object or None."""
        if not s or not s.strip():
            return None
        s = s.strip()
        try:
            return json.loads(s)
        except Exception:
            pass

        patterns = [r"(\[.*?\])", r"(\{.*?\})"]
        for pat in patterns:
            m = re.search(pat, s, re.DOTALL)
            if m:
                start = m.start(1)
                # Iterate backwards from the end of the string to find a valid JSON object
                for end in range(len(s), start, -1):
                    frag = s[start:end]
                    try:
                        return json.loads(frag)
                    except Exception:
                        continue
        return None

    def _parse_qa_lines(self, text: str) -> List[Dict[str, str]]:
        """Parse Q/A patterns from plain text."""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        qa_list: List[Dict[str, str]] = []
        q = None
        a_buf: List[str] = []

        def flush():
            nonlocal q, a_buf
            if q and a_buf:
                ans = " ".join(a_buf).strip()
                qa_list.append({"question": q.strip(), "answer": ans})
            q = None
            a_buf = []

        for ln in lines:
            if re.match(r'^(Q|Question)[:\.\s]', ln, re.I) or re.match(r'^\d+\.', ln):
                flush()
                q_text = re.sub(r'^(Q|Question)[:\.\s]*', '', ln, flags=re.I)
                q_text = re.sub(r'^\d+\.\s*', '', q_text)
                q = q_text
                continue
            if re.match(r'^(A|Answer)[:\.\s]', ln, re.I):
                a_text = re.sub(r'^(A|Answer)[:\.\s]*', '', ln, flags=re.I)
                a_buf.append(a_text)
                continue
            if ' A:' in ln or 'Answer:' in ln:
                parts = re.split(r'\sA[:ns]|Answer[:\s]', ln, maxsplit=1, flags=re.I)
                if parts and len(parts) >= 2:
                    q_part = re.sub(r'^(Q|Question)[:\.\s]*', '', parts[0], flags=re.I)
                    a_part = parts[1]
                    qa_list.append({"question": q_part.strip(), "answer": a_part.strip()})
                    q = None
                    a_buf = []
                    continue
            if q:
                a_buf.append(ln)
            elif ln.endswith('?'):
                flush()
                q = ln
        flush()
        return qa_list

    def _simple_keyword_extract(self, text: str, top_n: int = 5) -> List[str]:
        """Fallback keyword extraction."""
        try:
            from nltk.corpus import stopwords as sw
            stopwords = set(sw.words('english'))
        except Exception:
            stopwords = {"the", "and", "a", "in", "to", "of", "is", "it", "that", "for"}
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        freq: Dict[str, int] = {}
        for w in words:
            if w in stopwords:
                continue
            freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:top_n]]