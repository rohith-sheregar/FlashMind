import sys
import os
print("Python works")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../server')))
try:
    from app.main import app
    print("Imported app successfully")
except ImportError as e:
    print(f"Import failed: {e}")
