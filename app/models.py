import enum
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text
from sqlalchemy.sql import func
from app.database import Base


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class Priority(str, enum.Enum):
    HIGH = "high"
    LOW = "low"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    priority = Column(Enum(Priority), default=Priority.LOW, nullable=False)
    job_type = Column(String, nullable=False)        # e.g. "resize", "thumbnail"
    input_path = Column(String, nullable=False)
    output_path = Column(String, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)