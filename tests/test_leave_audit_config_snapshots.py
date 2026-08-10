from id_doc_ocr.leave_audit.domain.config import ConfigKind, ConfigSnapshot, ConfigStatus
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository


def test_config_snapshot_hash_is_stable_and_round_trips(tmp_path):
    repo = SQLiteRepository(tmp_path / "leave_audit.db")
    snapshot = ConfigSnapshot(
        version_id="cfg-ocr-1",
        kind=ConfigKind.OCR_PROFILE,
        content={"backend": "mock", "prompt": "extract fields"},
        created_by="engineer",
        change_reason="baseline",
    )
    repo.save_config_snapshot(snapshot)

    loaded = repo.get_config_snapshot("cfg-ocr-1")
    assert loaded is not None
    assert loaded.kind is ConfigKind.OCR_PROFILE
    assert loaded.status is ConfigStatus.DRAFT
    assert loaded.content_hash == snapshot.content_hash


def test_only_approved_config_can_be_published():
    snapshot = ConfigSnapshot("cfg-1", ConfigKind.DECISION_POLICY, {}, "engineer")
    try:
        snapshot.publish("approver")
    except ValueError as exc:
        assert "approved" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("draft config must not publish")

    snapshot.status = ConfigStatus.APPROVED
    snapshot.publish("approver")
    assert snapshot.status is ConfigStatus.PUBLISHED
    assert snapshot.approved_by == "approver"
    assert snapshot.published_at
