from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routes import router

app = FastAPI(title="TaskForge")
app.include_router(router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health_check():
    return {"status": "ok"}