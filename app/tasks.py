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


def _claim_job(db, job_id: str):
    """
    Atomically claim a QUEUED job for processing — idempotency guard for the
    FIRST delivery of a task message. A plain Python if-check (read status,
    then decide) has a gap where two near-simultaneous deliveries could both
    read QUEUED before either writes PROCESSING. This single UPDATE...WHERE
    closes that gap: only one execution can actually change the row.
    """
    rows_updated = (
        db.query(Job)
        .filter(Job.id == job_id, Job.status == JobStatus.QUEUED)
        .update({"status": JobStatus.PROCESSING}, synchronize_session=False)
    )
    db.commit()

    if rows_updated == 0:
        return None  # lost the race, or this job was never QUEUED to begin with

    return db.query(Job).filter(Job.id == job_id).first()


def _process_image_impl(job_id: str, is_first_attempt: bool):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        # Guard A: a duplicate delivery arriving for a job that already
        # reached a terminal state is definitely a duplicate — skip it.
        if job.status in (JobStatus.COMPLETED, JobStatus.DEAD_LETTER):
            print(f"[idempotency] job {job_id} already {job.status.value} — skipping duplicate delivery")
            return

        # Guard B: only the first delivery needs to atomically claim the job.
        # Celery's own self.retry() calls are intentional re-attempts on a
        # job we already claimed and left at PROCESSING — let those through.
        if is_first_attempt:
            job = _claim_job(db, job_id)
            if job is None:
                print(f"[idempotency] job {job_id} already claimed elsewhere — skipping")
                return

        # --- FAULT INJECTION: temporary, for testing retry logic only ---
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
            job.status = JobStatus.DEAD_LETTER
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
        raise

    finally:
        db.close()


def _run_with_retry(self, job_id: str):
    is_first_attempt = self.request.retries == 0
    try:
        _process_image_impl(job_id, is_first_attempt)
    except TransientProcessingError as exc:
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except MaxRetriesExceededError:
            db = SessionLocal()
            try:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.status = JobStatus.DEAD_LETTER
                    job.error_message = "Exceeded max retries (transient failures persisted)"
                    db.commit()
            finally:
                db.close()
    except PermanentProcessingError:
        return


@celery_app.task(bind=True, name="app.tasks.process_image_high", max_retries=3)
def process_image_high(self, job_id: str):
    _run_with_retry(self, job_id)


@celery_app.task(bind=True, name="app.tasks.process_image_low", max_retries=3)
def process_image_low(self, job_id: str):
    _run_with_retry(self, job_id)