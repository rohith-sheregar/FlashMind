import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def debug_login():
    print("🧪 Debugging Login...")
    
    # Use the credentials from the last successful signup (hardcoded for now as debug_signup uses randoms)
    # But wait, debug_signup used random credentials. I don't know them.
    # I should create a specific user for login test.
    
    username = "login_test_user"
    password = "password123"
    email = "login_test@example.com"
    
    # 1. Signup first
    print("   1. Signing up...")
    requests.post(f"{BASE_URL}/auth/signup", json={
        "username": username,
        "email": email,
        "password": password
    })
    
    # 2. Login
    print("   2. Logging in...")
    payload = {
        "username": username,
        "password": password
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", data=payload) # Form data
        print(f"   Status Code: {resp.status_code}")
        print(f"   Response Text: {resp.text}")
        
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            if token:
                print("   ✅ Login successful (Token received)")
            else:
                print("   ❌ Login failed (No token)")
        else:
            print("   ❌ Login failed")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    debug_login()
