from passlib.context import CryptContext

# Updated to use argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def test_hashing():
    print("🧪 Testing Hashing (Argon2)...")
    try:
        password = "password123"
        print(f"   Hashing password: '{password}'")
        hashed = pwd_context.hash(password)
        print(f"   ✅ Hashing successful: {hashed}")
        
        valid = pwd_context.verify(password, hashed)
        if valid:
            print("   ✅ Verification successful")
        else:
            print("   ❌ Verification failed")
            
    except Exception as e:
        print(f"   ❌ Hashing failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hashing()
