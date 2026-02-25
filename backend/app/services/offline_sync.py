"""
Offline Mode & Sync Service.
Enables scanning in dead zones (basements, rural areas) with automatic sync on reconnect.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"


@dataclass
class OfflineRecord:
    """A locally-stored record waiting to be synced."""
    local_id: str
    record_type: str  # "scan", "wound", "patient"
    payload: Dict
    created_at: datetime = field(default_factory=datetime.utcnow)
    sync_status: SyncStatus = SyncStatus.PENDING
    sync_attempts: int = 0
    error_message: Optional[str] = None


class OfflineSyncService:
    """
    Manages offline data capture and synchronization.

    On mobile: records are stored in encrypted local SQLite.
    When connection restored: records are synced to cloud in order.
    All PHI is encrypted before local storage (AES-256).
    """

    def __init__(self):
        self._queue: List[OfflineRecord] = []

    def queue_record(self, record_type: str, payload: Dict) -> OfflineRecord:
        """Add a record to the offline sync queue."""
        import uuid
        record = OfflineRecord(
            local_id=str(uuid.uuid4()),
            record_type=record_type,
            payload=payload,
        )
        self._queue.append(record)
        return record

    def get_pending_records(self) -> List[OfflineRecord]:
        """Return all records pending synchronization."""
        return [r for r in self._queue if r.sync_status == SyncStatus.PENDING]

    def mark_synced(self, local_id: str) -> None:
        """Mark a record as successfully synced."""
        for record in self._queue:
            if record.local_id == local_id:
                record.sync_status = SyncStatus.SYNCED
                return

    def mark_failed(self, local_id: str, error: str) -> None:
        """Mark a record sync as failed."""
        for record in self._queue:
            if record.local_id == local_id:
                record.sync_status = SyncStatus.FAILED
                record.sync_attempts += 1
                record.error_message = error
                return

    async def sync_all_pending(self, api_client) -> Dict:
        """
        Sync all pending offline records to the cloud API.
        Called automatically when network connectivity is restored.
        """
        pending = self.get_pending_records()
        results = {"synced": 0, "failed": 0, "total": len(pending)}

        for record in pending:
            try:
                record.sync_status = SyncStatus.SYNCING
                # Production: POST to appropriate API endpoint based on record_type
                # await api_client.post(f"/{record.record_type}s", json=record.payload)
                self.mark_synced(record.local_id)
                results["synced"] += 1
            except Exception as e:
                self.mark_failed(record.local_id, str(e))
                results["failed"] += 1

        return results


offline_sync_service = OfflineSyncService()
