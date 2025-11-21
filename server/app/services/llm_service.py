from transformers import pipeline
import re

class LLMService:
    _pipeline = None

    @classmethod
    def load_model(cls):
        if cls._pipeline is None:
            print("Loading LaMini-Flan-T5-77M...")
            try:
                cls._pipeline = pipeline(
                    "text2text-generation",
                    model="agentlans/LaMini-Flan-T5-77M-qa-generation",
                    max_new_tokens=256,
                    model_kwargs={
                        "do_sample": True, 
                        "temperature": 0.1, 
                        "repetition_penalty": 2.0, 
                        "no_repeat_ngram_size": 3
                    }
                )
                print("✅ Model loaded successfully.")
            except Exception as e:
                print(f"❌ Model load failed: {e}")

    def generate_flashcards(self, context_text: str):
        if LLMService._pipeline is None:
            LLMService.load_model()
        
        if not LLMService._pipeline:
            return []

        input_text = f"generate a question and answer from this text: {context_text}"
        
        results = LLMService._pipeline(input_text)
        raw_output = results[0]['generated_text']
        
        print(f"\n🤖 [RAW LLM OUTPUT]: {raw_output}\n") 

        # --- FIX: ARTIFACT CLEANER ---
        # Remove the specific tags BEFORE processing anything else
        clean_text = raw_output.replace("[QUESTION_END]", "").replace("[ANSWER_END]", "").strip()
        
        cards = []

        # 1. Split by Question Mark
        if "?" in clean_text:
            parts = clean_text.split("?")
            
            # Question is everything before the ?
            question = parts[0].strip() + "?"
            
            # Answer is everything after
            raw_answer_rest = " ".join(parts[1:]).strip()
            
            # Take only the first sentence of the answer to keep it clean
            if "." in raw_answer_rest:
                answer = raw_answer_rest.split(".")[0] + "."
            else:
                answer = raw_answer_rest

            if len(question) > 5 and len(answer) > 5:
                cards.append({
                    "front": question,
                    "back": answer
                })
        
        # 2. Fallback Regex
        else:
            match = re.search(r"(?:Question|Q)[:\s]+(.*?)(?:Answer|A)[:\s]+(.*)", clean_text, re.IGNORECASE)
            if match:
                q = match.group(1).strip()
                a_full = match.group(2).strip()
                a_clean = a_full.split(".")[0] + "."
                cards.append({"front": q, "back": a_clean})

        # 3. Last Resort
        if not cards and len(clean_text) > 10:
            first_sentence = clean_text.split(".")[0] + "."
            cards.append({
                "front": "Key Concept",
                "back": first_sentence
            })

        return cards