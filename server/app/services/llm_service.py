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
                        # CRITICAL: High penalty prevents the model from using the same words twice
                        "repetition_penalty": 2.0, 
                        "no_repeat_ngram_size": 3 # Hard block on repeating 3-word phrases
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

        cards = []

        # --- STRICT CLEANER LOGIC ---
        
        # 1. Identify the split between Question and Answer
        # The model usually outputs: "Question? Answer."
        if "?" in raw_output:
            parts = raw_output.split("?")
            
            # Part 1: The Question (Before the ?)
            question = parts[0].strip() + "?"
            
            # Part 2: The Answer (After the ?)
            # THE FIX: We take ONLY the first sentence of the answer.
            # We split by "." and take the first part.
            raw_answer_rest = " ".join(parts[1:]).strip()
            
            if "." in raw_answer_rest:
                answer = raw_answer_rest.split(".")[0] + "."
            else:
                # If there is no period, just take the first 100 chars to be safe
                answer = raw_answer_rest[:100]

            # Basic validation to ensure we don't save empty garbage
            if len(question) > 5 and len(answer) > 5:
                cards.append({
                    "front": question,
                    "back": answer
                })
        
        # 2. Fallback: If no '?' found, try to regex search
        else:
            # Look for "Question:" label explicitly
            match = re.search(r"(?:Question|Q)[:\s]+(.*?)(?:Answer|A)[:\s]+(.*)", raw_output, re.IGNORECASE)
            if match:
                q = match.group(1).strip()
                a_full = match.group(2).strip()
                # Again, strictly take only the first sentence of the answer
                a_clean = a_full.split(".")[0] + "."
                cards.append({"front": q, "back": a_clean})

        # 3. Last Resort: Saving raw text (Truncated)
        if not cards and len(raw_output) > 10:
            # Just save the first sentence of the raw output
            first_sentence = raw_output.split(".")[0] + "."
            cards.append({
                "front": "Key Concept",
                "back": first_sentence
            })

        return cards