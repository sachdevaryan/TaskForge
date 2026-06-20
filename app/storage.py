import os
import uuid
from app.config import settings


def save_upload(file_bytes: bytes, original_filename: str) -> str:
    """Saves uploaded bytes to disk, returns the path where they live."""
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)

    ext = os.path.splitext(original_filename)[1]  # e.g. ".jpg"
    stored_name = f"{uuid.uuid4()}{ext}"
    full_path = os.path.join(settings.STORAGE_DIR, stored_name)

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    return full_path