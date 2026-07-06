import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load the env from backend_flask
load_dotenv(os.path.join("backend_flask", ".env"))

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("Error: OPENROUTER_API_KEY not found in backend_flask/.env")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

models_to_test = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-1.5-flash",
    "openai/gpt-4o-mini",
    "mistralai/mistral-nemo:free",
    "deepseek/deepseek-chat:free"
]

system_prompt = "You are an expert tutor. Summarize the following concept accurately in exactly two short sentences."
user_prompt = "Concept: The process of photosynthesis in plants, specifically how they convert light energy into chemical energy."

print("Starting OpenRouter Model Smoke Test...\n")

best_model = None
best_time = float('inf')

for model in models_to_test:
    print(f"Testing model: {model}")
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=150,
        )
        elapsed_time = time.time() - start_time
        content = response.choices[0].message.content.strip()
        print(f"  [SUCCESS] Time: {elapsed_time:.2f}s")
        print(f"  [RESPONSE]: {content}\n")
        
        if elapsed_time < best_time:
            best_time = elapsed_time
            best_model = model
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"  [FAILED] Time: {elapsed_time:.2f}s")
        print(f"  [ERROR]: {e}\n")

print(f"Test Complete. Fastest working model: {best_model} ({best_time:.2f}s)")
