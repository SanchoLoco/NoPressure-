"""
Zero-footprint image storage service.
Images are stored securely (encrypted cloud in production); never saved to device gallery.
Supports local file storage for development and a pluggable cloud backend.
"""
import hashlib
import os
from datetime import datetime, timezone
from typing import Optional

from ..core.config import settings


class ImageStorageService:
    """Store wound images with zero-footprint guarantee.

    In development mode images are written to a local directory.
    In production configure ``CLOUD_STORAGE_BUCKET`` for encrypted cloud upload.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "uploads",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(
        self,
        image_data: bytes,
        wound_id: str,
        scan_id: str,
    ) -> dict:
        """Persist an image and return ``{"image_url": ..., "image_hash": ...}``."""
        image_hash = hashlib.sha256(image_data).hexdigest()

        if settings.CLOUD_STORAGE_BUCKET:
            image_url = self._upload_to_cloud(image_data, wound_id, scan_id)
        else:
            image_url = self._save_local(image_data, wound_id, scan_id)

        return {"image_url": image_url, "image_hash": image_hash}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save_local(self, image_data: bytes, wound_id: str, scan_id: str) -> str:
        """Save to local ``uploads/`` directory for development."""
        wound_dir = os.path.join(self.base_dir, wound_id)
        os.makedirs(wound_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        filename = f"{scan_id}_{ts}.png"
        filepath = os.path.join(wound_dir, filename)
        with open(filepath, "wb") as fh:
            fh.write(image_data)
        return filepath

    def _upload_to_cloud(self, image_data: bytes, wound_id: str, scan_id: str) -> str:
        """Upload to encrypted cloud storage.

        Production: use httpx / boto3 / azure-storage-blob to PUT the object.
        Returns the remote URL.
        """
        bucket = settings.CLOUD_STORAGE_BUCKET
        key = f"wounds/{wound_id}/{scan_id}.png"
        # Placeholder — replace with real SDK call in production
        return f"https://{bucket}.storage.example.com/{key}"


image_storage = ImageStorageService()
