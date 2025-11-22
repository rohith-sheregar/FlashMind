import sys
import os

# Add server directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../server')))

from fastapi.testclient import TestClient
from app.main import app
from app.services.db_setup import Base, engine, SessionLocal
from app.models.user import User
import uuid

client = TestClient(app)

def test_auth_flow_client():
    print("🧪 Starting Auth Flow Test (TestClient)...")
    
    # 1. Signup
    suffix = str(uuid.uuid4())[:8]
    username = f"user_{suffix}"
    email = f"user_{suffix}@example.com"
    password = "password123"
    
    print(f"   Attempting signup for {username}...")
    signup_resp = client.post("/api/auth/signup", json={
        "username": username,
        "email": email,
        "password": password
    })
    
    if signup_resp.status_code == 201 or signup_resp.status_code == 200:
        print("   ✅ Signup successful")
    else:
        print(f"   ❌ Signup failed: {signup_resp.status_code} - {signup_resp.text}")
        return

    # 2. Login
    print("   Attempting login...")
    login_resp = client.post("/api/auth/login", data={
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
    me_resp = client.get("/api/auth/me", headers=headers)
    
    if me_resp.status_code == 200:
        print(f"   ✅ /auth/me successful: {me_resp.json()}")
    else:
        print(f"   ❌ /auth/me failed: {me_resp.status_code} - {me_resp.text}")
        
    # 4. Verify Protected Route (/decks/1)
    print("   Verifying protected deck route...")
    deck_resp = client.get("/api/decks/99999", headers=headers)
    
    if deck_resp.status_code == 401:
        print("   ❌ Protected route returned 401 Unauthorized")
    else:
        print(f"   ✅ Protected route accessed (Status: {deck_resp.status_code}) - Auth middleware working")

if __name__ == "__main__":
    try:
        test_auth_flow_client()
    except Exception as e:
        print(f"❌ Test script error: {e}")
