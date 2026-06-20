from fastapi import FastAPI

app = FastAPI(title="TaskForge")

@app.get("/health")
def health_check():
    return {"status": "ok"}