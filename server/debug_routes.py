from app.main import app
import sys

print("🔍 Registered Routes:")
for route in app.routes:
    if "auth" in route.path:
        methods = ", ".join(route.methods) if hasattr(route, "methods") else "None"
        print(f"   {methods} {route.path}")
