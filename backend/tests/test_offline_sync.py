from app.services.offline_sync import OfflineSyncService, SyncStatus


def test_queue_and_retrieve_record():
    """Records queued offline should be retrievable as pending."""
    service = OfflineSyncService()
    record = service.queue_record("scan", {"wound_id": "w1", "area_cm2": 5.0})
    pending = service.get_pending_records()
    assert len(pending) == 1
    assert pending[0].local_id == record.local_id
    assert pending[0].sync_status == SyncStatus.PENDING


def test_mark_synced():
    """Marking a record synced should remove it from pending."""
    service = OfflineSyncService()
    record = service.queue_record("scan", {"wound_id": "w1"})
    service.mark_synced(record.local_id)
    pending = service.get_pending_records()
    assert len(pending) == 0


def test_mark_failed():
    """Marking a record failed should update status and error message."""
    service = OfflineSyncService()
    record = service.queue_record("scan", {"wound_id": "w1"})
    service.mark_failed(record.local_id, "Network timeout")
    pending = service.get_pending_records()
    assert len(pending) == 0  # Failed records not in pending
    failed = [r for r in service._queue if r.sync_status == SyncStatus.FAILED]
    assert len(failed) == 1
    assert failed[0].error_message == "Network timeout"


def test_multiple_records_queue():
    """Multiple records should all be queued and retrievable."""
    service = OfflineSyncService()
    service.queue_record("scan", {"wound_id": "w1"})
    service.queue_record("scan", {"wound_id": "w2"})
    service.queue_record("patient", {"mrn": "MRN123"})
    pending = service.get_pending_records()
    assert len(pending) == 3
