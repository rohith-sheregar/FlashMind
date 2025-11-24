from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import re
import torch
from typing import List, Dict, Generator

class LLMService:
    _pipeline = None
    _model = None
    _tokenizer = None

    @classmethod
    def load_model(cls):
        if cls._pipeline is None:
            print("🤖 Loading LaMini-Flan-T5-77M-qa-generation...")
            try:
                model_name = "agentlans/LaMini-Flan-T5-77M-qa-generation"
                
                # Load tokenizer and model separately for better control
                cls._tokenizer = AutoTokenizer.from_pretrained(model_name)
                cls._model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                # Create pipeline with optimized settings
                cls._pipeline = pipeline(
                    "text2text-generation",
                    model=cls._model,
                    tokenizer=cls._tokenizer,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3,
                    early_stopping=True,
                    device=0 if torch.cuda.is_available() else -1
                )
                print("✅ Model loaded successfully.")
                print(f"📊 Using device: {'GPU' if torch.cuda.is_available() else 'CPU'}")
            except Exception as e:
                print(f"❌ Model load failed: {e}")

    def generate_flashcards_batch(self, chunks: List[str]) -> Generator[Dict[str, str], None, None]:
        """Generate flashcards from multiple chunks, yielding results as they're ready"""
        if LLMService._pipeline is None:
            LLMService.load_model()
        
        if not LLMService._pipeline:
            return
        
        for i, chunk in enumerate(chunks):
            print(f"🔄 Processing chunk {i+1}/{len(chunks)}...")
            cards = self.generate_flashcards(chunk)
            for card in cards:
                yield card

    def generate_flashcards(self, context_text: str) -> List[Dict[str, str]]:
        """Generate flashcards from a single text chunk"""
        if LLMService._pipeline is None:
            LLMService.load_model()
        
        if not LLMService._pipeline or not context_text.strip():
            return []

        # Enhanced prompt for better results
        input_text = f"""Generate question and answer pairs from this educational content. Create clear, specific questions that test understanding of key concepts:

{context_text}

Format: Question[QUESTION_END]Answer[ANSWER_END]"""
        
        try:
            results = LLMService._pipeline(input_text)
            raw_output = results[0]['generated_text']
            
            print(f"🤖 [RAW OUTPUT]: {raw_output[:200]}...")
            
            # Parse the output using the model's expected format
            cards = self._parse_qa_pairs(raw_output)
            
            # If no cards found, try alternative parsing
            if not cards:
                cards = self._fallback_parsing(raw_output, context_text)
            
            print(f"✅ Generated {len(cards)} flashcards from chunk")
            return cards
            
        except Exception as e:
            print(f"❌ Error generating flashcards: {e}")
            return []

    def _parse_qa_pairs(self, input_text: str) -> List[Dict[str, str]]:
        """Parse Q&A pairs using the model's expected format"""
        def clean_text(text):
            return re.sub(r'\s+', ' ', text).strip()

        qa_blocks = re.split(r'(\[ANSWER_END\])', input_text)
        pairs = []
        
        for i in range(0, len(qa_blocks) - 1, 2):
            qa_block = qa_blocks[i]
            parts = qa_block.split('[QUESTION_END]')
            
            if len(parts) == 2:
                question = clean_text(parts[0])
                answer = clean_text(parts[1])
                
                # Clean up question and answer
                question = self._clean_question(question)
                answer = self._clean_answer(answer)
                
                if question and answer and len(question) > 10 and len(answer) > 10:
                    pairs.append({
                        "front": question,
                        "back": answer
                    })
        
        return pairs

    def _fallback_parsing(self, raw_output: str, context_text: str) -> List[Dict[str, str]]:
        """Fallback parsing methods when standard format fails"""
        cards = []
        
        # Remove special tokens
        clean_text = raw_output.replace("[QUESTION_END]", "").replace("[ANSWER_END]", "").strip()
        
        # Method 1: Look for question patterns
        question_patterns = [
            r'(?:Question|Q)[:.]?\s*(.+?\?)\s*(?:Answer|A)[:.]?\s*(.+?)(?=Question|Q|$)',
            r'(.+?\?)\s*(.+?)(?=\?|$)',
            r'What\s+(.+?\?)\s*(.+?)(?=What|$)',
            r'How\s+(.+?\?)\s*(.+?)(?=How|$)',
            r'Why\s+(.+?\?)\s*(.+?)(?=Why|$)'
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, clean_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match) == 2:
                    question = self._clean_question(match[0])
                    answer = self._clean_answer(match[1])
                    
                    if question and answer and len(question) > 10 and len(answer) > 10:
                        cards.append({
                            "front": question,
                            "back": answer
                        })
                        break
        
        # Method 2: Generate from context if no cards found
        if not cards and len(context_text) > 50:
            # Extract key sentences for basic Q&A
            sentences = [s.strip() for s in context_text.split('.') if len(s.strip()) > 20]
            if sentences:
                # Create a simple factual question
                first_sentence = sentences[0]
                if len(first_sentence) > 30:
                    # Try to create a "What is..." question
                    words = first_sentence.split()
                    if len(words) > 5:
                        subject = ' '.join(words[:3])
                        cards.append({
                            "front": f"What can you tell me about {subject.lower()}?",
                            "back": first_sentence + "."
                        })
        
        return cards

    def _clean_question(self, question: str) -> str:
        """Clean and format questions"""
        question = question.strip()
        
        # Remove common prefixes
        prefixes = ['generate a question and answer from this text:', 'question:', 'q:']
        for prefix in prefixes:
            if question.lower().startswith(prefix):
                question = question[len(prefix):].strip()
        
        # Ensure question ends with question mark
        if not question.endswith('?'):
            question += '?'
        
        # Capitalize first letter
        if question:
            question = question[0].upper() + question[1:]
        
        return question

    def _clean_answer(self, answer: str) -> str:
        """Clean and format answers"""
        answer = answer.strip()
        
        # Remove common prefixes
        prefixes = ['answer:', 'a:', 'the answer is:', 'it is:']
        for prefix in prefixes:
            if answer.lower().startswith(prefix):
                answer = answer[len(prefix):].strip()
        
        # Ensure answer ends with period
        if answer and not answer.endswith(('.', '!', '?')):
            answer += '.'
        
        # Capitalize first letter
        if answer:
            answer = answer[0].upper() + answer[1:]
        
        # Limit answer length
        if len(answer) > 300:
            sentences = answer.split('.')
            answer = '. '.join(sentences[:2]) + '.'
        
        return answer

    def generate_quiz(self, cards: List[Dict[str, str]]) -> Dict[str, any]:
        """Generate a multiple choice quiz from a list of flashcards"""
        if LLMService._pipeline is None:
            LLMService.load_model()
            
        if not LLMService._pipeline or not cards:
            return None

        # Combine cards into a context
        # Limit context to avoid token limits, pick random 5 cards if more
        import random
        selected_cards = cards if len(cards) <= 5 else random.sample(cards, 5)
        context = " ".join([f"Q: {c['front']} A: {c['back']}" for c in selected_cards])
        
        prompt = f"""Create a multiple choice question based on this context:
{context}

Response format:
Question: ...
A) ...
B) ...
C) ...
D) ...
Correct Answer: ...
"""

        try:
            results = LLMService._pipeline(prompt)
            raw_output = results[0]['generated_text']
            print(f"🤖 [QUIZ RAW]: {raw_output}")
            
            quiz = self._parse_quiz(raw_output)
            if not quiz:
                print("⚠️ Standard parsing failed, attempting fallback...")
                quiz = self._fallback_quiz_parsing(raw_output)
            
            if not quiz:
                print("⚠️ LLM failed completely, using deterministic fallback...")
                quiz = self._generate_deterministic_quiz(cards)

            return quiz
        except Exception as e:
            print(f"❌ Error generating quiz: {e}")
            # Final safety net
            return self._generate_deterministic_quiz(cards)

    def _parse_quiz(self, raw_output: str) -> Dict[str, any]:
        """Parse the quiz output with improved robustness"""
        try:
            lines = [line.strip() for line in raw_output.split('\n') if line.strip()]
            question = ""
            options = {}
            correct_answer = ""
            
            current_mode = None
            
            for line in lines:
                # Handle Question
                if line.lower().startswith("question:"):
                    question = line[9:].strip()
                    continue
                
                # Handle Options
                # Match A) or A. or (A)
                option_match = re.match(r'^([A-D])[\)\.]\s*(.+)', line, re.IGNORECASE)
                if option_match:
                    opt_char = option_match.group(1).upper()
                    opt_text = option_match.group(2).strip()
                    options[opt_char] = opt_text
                    continue
                
                # Handle Correct Answer
                if "correct answer" in line.lower():
                    # Extract just the letter
                    ans_match = re.search(r'([A-D])', line.split(":")[-1], re.IGNORECASE)
                    if ans_match:
                        correct_answer = ans_match.group(1).upper()
                    continue
            
            # Validation
            if question and len(options) >= 2 and correct_answer:
                # Ensure correct answer is in options
                if correct_answer not in options:
                    print(f"⚠️ Correct answer {correct_answer} not found in options {list(options.keys())}")
                    return None
                    
                return {
                    "question": question,
                    "options": options,
                    "correct_answer": correct_answer
                }
            return None
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return None

    def _fallback_quiz_parsing(self, raw_output: str) -> Dict[str, any]:
        """Try to salvage a quiz from malformed output"""
        try:
            # 1. Try to find the question (usually the first line or starts with Q)
            lines = [l.strip() for l in raw_output.split('\n') if l.strip()]
            if not lines:
                return None
                
            question = lines[0]
            if question.lower().startswith("question:"):
                question = question[9:].strip()
            
            # 2. Extract options using regex from the whole text
            options = {}
            # Look for patterns like A) ... B) ...
            # or A. ... B. ...
            for char in ['A', 'B', 'C', 'D']:
                pattern = f"{char}[\)\.]\s*([^A-D\n]+)"
                match = re.search(pattern, raw_output, re.IGNORECASE)
                if match:
                    options[char] = match.group(1).strip()
            
            # 3. Extract correct answer
            correct_answer = "A" # Default fallback if we can't find it
            ans_match = re.search(r'Correct Answer:?\s*([A-D])', raw_output, re.IGNORECASE)
            if ans_match:
                correct_answer = ans_match.group(1).upper()
            
            if question and len(options) >= 2:
                return {
                    "question": question,
                    "options": options,
                    "correct_answer": correct_answer
                }
            return None
        except Exception:
            return None

    def _generate_deterministic_quiz(self, cards: List[Dict[str, str]]) -> Dict[str, any]:
        """Generate a quiz deterministically from cards if LLM fails"""
        try:
            if not cards:
                return None
            
            import random
            
            # Pick a correct answer card
            correct_card = random.choice(cards)
            question = correct_card['front']
            correct_answer_text = correct_card['back']
            
            # Pick distractors
            other_cards = [c for c in cards if c != correct_card]
            distractors = []
            if len(other_cards) >= 3:
                distractors = [c['back'] for c in random.sample(other_cards, 3)]
            else:
                # Not enough cards for real distractors, duplicate or make up
                distractors = [c['back'] for c in other_cards]
                while len(distractors) < 3:
                    distractors.append("None of the above")
            
            # Combine and shuffle
            all_options = distractors + [correct_answer_text]
            random.shuffle(all_options)
            
            # Map to A, B, C, D
            options_map = {}
            correct_letter = ""
            for i, letter in enumerate(['A', 'B', 'C', 'D']):
                if i < len(all_options):
                    options_map[letter] = all_options[i]
                    if all_options[i] == correct_answer_text:
                        correct_letter = letter
            
            return {
                "question": question,
                "options": options_map,
                "correct_answer": correct_letter
            }
        except Exception as e:
            print(f"❌ Deterministic fallback failed: {e}")
            return None