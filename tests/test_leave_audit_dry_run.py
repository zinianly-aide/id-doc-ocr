from pathlib import Path

from fastapi.testclient import TestClient

from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.async_status import CallbackStatus, DecisionStatus
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAuditResult, LeaveAuditTask
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.service.app import ServiceSettings, create_app


class RecordingAdapter(LeaveSystemAdapter):
    def __init__(self) -> None:
        self.pushed: list[LeaveAuditResult] = []

    def fetch_pending_attachments(self) -> list[LeaveAuditTask]:
        return []

    def download_attachment(self, attachment_url: str) -> bytes:
        return b"fake-image"

    def push_audit_result(self, result: LeaveAuditResult) -> None:
        self.pushed.append(result)


def build_client(tmp_path: Path, adapter: RecordingAdapter) -> tuple[TestClient, SQLiteRepository]:
    app = create_app(
        ServiceSettings(
            default_ocr_backend="mock",
            default_vlm_backend="mock",
            default_detector_backend="mock",
            default_rectify_backend="mock",
        )
    )
    repo = SQLiteRepository(tmp_path / "leave_audit.db")
    app.state.leave_audit_repository = repo
    app.state.leave_system_adapter = adapter
    return TestClient(app), repo


def seed_result(repo: SQLiteRepository) -> None:
    repo.save_task(LeaveAuditTask(request_id="LV-DRY-001", leave_type="SICK", employee_name="张三"))
    repo.save_result(
        LeaveAuditResult(
            request_id="LV-DRY-001",
            status=LeaveAuditStatus.REVIEW,
            verification_json={
                "verify_status": "REVIEW",
                "risk_level": "MEDIUM",
                "risk_score": 30,
                "needs_manual_review": True,
                "summary_message": "needs review",
                "rule_results": [{"rule_code": "applicant_name_match", "passed": False}],
                "evidence": {"request": {"leave_request_id": "LR-DRY-001"}},
            },
        )
    )


def test_dry_run_callback_skips_real_adapter_and_returns_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN", "true")
    adapter = RecordingAdapter()
    client, repo = build_client(tmp_path, adapter)
    seed_result(repo)

    response = client.post("/leave-audit/tasks/LV-DRY-001/callback")

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert payload["callback_skipped"] is True
    assert payload["callback_payload"]["leave_request_id"] == "LR-DRY-001"
    assert adapter.pushed == []
    saved = repo.get_result("LV-DRY-001")
    assert saved.verification_json["callback_dry_run"]["payload"]["request_id"] == "LV-DRY-001"
    assert repo.get_task("LV-DRY-001").status == LeaveAuditStatus.PENDING


def test_non_dry_run_callback_calls_adapter_and_marks_synced(tmp_path, monkeypatch):
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN", "false")
    adapter = RecordingAdapter()
    client, repo = build_client(tmp_path, adapter)
    seed_result(repo)

    response = client.post("/leave-audit/tasks/LV-DRY-001/callback")

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is False
    assert payload["callback_skipped"] is False
    assert len(adapter.pushed) == 1
    result = repo.get_result("LV-DRY-001")
    task = repo.get_task("LV-DRY-001")
    assert result.synced is True
    assert result.callback_status is CallbackStatus.SUCCEEDED
    assert task.status == LeaveAuditStatus.PENDING
    assert task.decision_status is DecisionStatus.PENDING
    assert task.callback_status is CallbackStatus.SUCCEEDED
