from fastapi import FastAPI

app = FastAPI(title="FlashMind API")

@app.get("/")
def read_root():
    return {"message": "Welcome to FlashMind API"}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}