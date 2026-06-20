from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models import JobStatus, Priority


class JobResponse(BaseModel):
    id: str
    status: JobStatus
    priority: Priority
    job_type: str
    retry_count: int
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True  