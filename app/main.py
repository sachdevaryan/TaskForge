from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TaskForge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health_check():
    return {"status": "ok"}