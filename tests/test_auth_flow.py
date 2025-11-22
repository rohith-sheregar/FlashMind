import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def test_auth_flow():
    print("🧪 Starting Auth Flow Test...")
    
    # 1. Signup
    username = "testuser_new"
    email = "testuser_new@example.com"
    password = "password123"
    
    print(f"   Attempting signup for {username}...")
    signup_resp = requests.post(f"{BASE_URL}/auth/signup", json={
        "username": username,
        "email": email,
        "password": password
    })
    
    if signup_resp.status_code == 201 or signup_resp.status_code == 200:
        print("   ✅ Signup successful")
    elif signup_resp.status_code == 400 and "already registered" in signup_resp.text:
         print("   ℹ️ User already exists, proceeding to login")
    else:
        print(f"   ❌ Signup failed: {signup_resp.status_code} - {signup_resp.text}")
        return

    # 2. Login
    print("   Attempting login...")
    login_resp = requests.post(f"{BASE_URL}/auth/login", data={
        "username": username,
        "password": password
    })
    
    if login_resp.status_code != 200:
        print(f"   ❌ Login failed: {login_resp.status_code} - {login_resp.text}")
        return
        
    data = login_resp.json()
    token = data.get("access_token")
    user = data.get("user")
    
    if not token or not user:
        print("   ❌ Login response missing token or user data")
        return
        
    print(f"   ✅ Login successful. Token received. User ID: {user['id']}")
    
    # 3. Verify Protected Route (/auth/me)
    print("   Verifying /auth/me...")
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if me_resp.status_code == 200:
        print(f"   ✅ /auth/me successful: {me_resp.json()}")
    else:
        print(f"   ❌ /auth/me failed: {me_resp.status_code} - {me_resp.text}")
        
    # 4. Verify Protected Route (/decks/1) - assuming deck 1 exists or we get 404 but authorized
    # We need to create a deck first or check existing.
    # Let's try to access a deck. If we get 401, it failed. If we get 404 or 200, auth worked.
    print("   Verifying protected deck route...")
    deck_resp = requests.get(f"{BASE_URL}/decks/99999", headers=headers)
    
    if deck_resp.status_code == 401:
        print("   ❌ Protected route returned 401 Unauthorized")
    else:
        print(f"   ✅ Protected route accessed (Status: {deck_resp.status_code}) - Auth middleware working")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except Exception as e:
        print(f"❌ Test script error: {e}")
