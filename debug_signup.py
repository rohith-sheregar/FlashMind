import requests
import sys
import uuid

BASE_URL = "http://127.0.0.1:8000/api"

def debug_signup():
    print("🧪 Debugging Signup...")
    
    suffix = str(uuid.uuid4())[:8]
    username = f"debug_user_{suffix}"
    email = f"debug_{suffix}@example.com"
    password = "password123"
    
    payload = {
        "username": username,
        "email": email,
        "password": password
    }
    
    print(f"   Sending payload: {payload}")
    
    try:
        resp = requests.post(f"{BASE_URL}/auth/signup", json=payload)
        print(f"   Status Code: {resp.status_code}")
        print(f"   Response Text: {resp.text}")
        
        if resp.status_code == 201 or resp.status_code == 200:
            print("   ✅ Signup successful")
        else:
            print("   ❌ Signup failed")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    debug_signup()
