try:
    import argon2
    print(f"✅ argon2 imported: {argon2.__version__}")
except ImportError as e:
    print(f"❌ argon2 import failed: {e}")

try:
    import passlib
    print(f"✅ passlib imported: {passlib.__version__}")
except ImportError as e:
    print(f"❌ passlib import failed: {e}")
