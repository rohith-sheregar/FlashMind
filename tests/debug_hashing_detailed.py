import sys
try:
    import bcrypt
    print(f"✅ bcrypt imported: {bcrypt.__version__}")
except ImportError as e:
    print(f"❌ bcrypt import failed: {e}")

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_hashing():
    print("🧪 Testing Hashing Detailed...")
    try:
        password = "password123"
        print(f"   Hashing password: '{password}'")
        hashed = pwd_context.hash(password)
        print(f"   ✅ Hashing successful: {hashed}")
    except Exception as e:
        print(f"   ❌ Hashing failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hashing()
