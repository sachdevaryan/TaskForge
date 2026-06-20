import random
from datetime import datetime, timezone
from PIL import Image, UnidentifiedImageError
from celery.exceptions import MaxRetriesExceededError
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Job, JobStatus


class TransientProcessingError(Exception):
    """Worth retrying — likely to succeed if we try again shortly."""


class PermanentProcessingError(Exception):
    """Never worth retrying — the input itself is unprocessable."""


def _process_image_impl(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = JobStatus.PROCESSING
        db.commit()

        # --- FAULT INJECTION: temporary, for testing retry logic only ---
        # In production this would be a real flaky dependency (e.g. an S3 write,
        # a virus-scan API call). We don't have one yet, so we simulate it:
        # fail the first 2 attempts deterministically, succeed on the 3rd.
        if job.retry_count < 2:
            raise TransientProcessingError(
                "Simulated transient failure (e.g. flaky storage write)"
            )

        output_path = f"{job.input_path}_thumb.jpg"
        try:
            with Image.open(job.input_path) as img:
                img.thumbnail((200, 200))
                img.convert("RGB").save(output_path, "JPEG")
        except UnidentifiedImageError as exc:
            job.status = JobStatus.FAILED
            job.error_message = f"Corrupted or unsupported image: {exc}"
            db.commit()
            raise PermanentProcessingError(str(exc))

        job.status = JobStatus.COMPLETED
        job.output_path = output_path
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except TransientProcessingError:
        job.retry_count += 1
        job.error_message = "Transient failure — retrying"
        db.commit()
        raise  # let the task wrapper decide whether to actually retry

    finally:
        db.close()


def _run_with_retry(self, job_id: str):
    try:
        _process_image_impl(job_id)
    except TransientProcessingError as exc:
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except MaxRetriesExceededError:
            db = SessionLocal()
            try:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.status = JobStatus.FAILED
                    job.error_message = "Exceeded max retries (transient failures persisted)"
                    db.commit()
            finally:
                db.close()
    except PermanentProcessingError:
        return  # already marked FAILED inside _process_image_impl


@celery_app.task(bind=True, name="app.tasks.process_image_high", max_retries=3)
def process_image_high(self, job_id: str):
    _run_with_retry(self, job_id)


@celery_app.task(bind=True, name="app.tasks.process_image_low", max_retries=3)
def process_image_low(self, job_id: str):
    _run_with_retry(self, job_id)