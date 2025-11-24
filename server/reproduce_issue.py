import requests
import json

def test_quiz_generation():
    url = "http://localhost:8001/api/quiz/generate"
    payload = {
        "cards": [
            {"front": "What is the capital of France?", "back": "Paris"},
            {"front": "What is the largest planet in our solar system?", "back": "Jupiter"},
            {"front": "Who wrote Romeo and Juliet?", "back": "William Shakespeare"},
            {"front": "What is the chemical symbol for water?", "back": "H2O"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response:", json.dumps(response.json(), indent=2))
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_quiz_generation()
