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