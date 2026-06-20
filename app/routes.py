from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job, JobStatus, Priority
from app.schemas import JobResponse
from app.storage import save_upload
from app.celery_app import celery_app

router = APIRouter()


@router.post("/jobs", response_model=JobResponse)
async def create_job(
    file: UploadFile = File(...),
    priority: Priority = Form(Priority.LOW),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    input_path = save_upload(file_bytes, file.filename)

    job = Job(
        job_type="resize",
        input_path=input_path,
        status=JobStatus.QUEUED,
        priority=priority,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    task_name = (
        "app.tasks.process_image_high"
        if priority == Priority.HIGH
        else "app.tasks.process_image_low"
    )
    celery_app.send_task(task_name, args=[job.id])

    return job


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job