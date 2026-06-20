from datetime import datetime, timezone
from PIL import Image
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Job, JobStatus


@celery_app.task(name="app.tasks.process_image")
def process_image(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return  

        job.status = JobStatus.PROCESSING
        db.commit()

        output_path = f"{job.input_path}_thumb.jpg"
        with Image.open(job.input_path) as img:
            img.thumbnail((200, 200))
            img.convert("RGB").save(output_path, "JPEG")

        job.status = JobStatus.COMPLETED
        job.output_path = output_path
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()