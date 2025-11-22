from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_hashing():
    print("🧪 Testing Hashing...")
    try:
        password = "password123"
        hashed = pwd_context.hash(password)
        print(f"   ✅ Hashing successful: {hashed[:10]}...")
        
        valid = pwd_context.verify(password, hashed)
        if valid:
            print("   ✅ Verification successful")
        else:
            print("   ❌ Verification failed")
            
    except Exception as e:
        print(f"   ❌ Hashing failed: {e}")

if __name__ == "__main__":
    test_hashing()
