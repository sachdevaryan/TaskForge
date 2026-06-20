import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://taskforge:taskforge@db:5432/taskforge")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "/app/storage")
    SIMULATE_TRANSIENT_FAILURE_RATE: float = float(os.getenv("SIMULATE_TRANSIENT_FAILURE_RATE", "0"))

settings = Settings()