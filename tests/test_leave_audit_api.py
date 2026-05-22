from pathlib import Path

from fastapi.testclient import TestClient

from id_doc_ocr.leave_audit.adapters.mock_leave_system import MockLeaveSystemAdapter
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.service.app import ServiceSettings, create_app


def build_client(tmp_path: Path) -> TestClient:
    app = create_app(ServiceSettings(default_ocr_backend="mock", default_vlm_backend="mock", default_detector_backend="mock", default_rectify_backend="mock"))
    app.state.leave_audit_repository = SQLiteRepository(tmp_path / "leave_audit.db")
    app.state.leave_system_adapter = MockLeaveSystemAdapter()
    return TestClient(app)


def test_leave_audit_api_sync_list_detail_run_and_review(tmp_path):
    client = build_client(tmp_path)

    sync = client.post("/leave-audit/sync")
    assert sync.status_code == 200
    assert sync.json()["synced"] >= 3

    listing = client.get("/leave-audit/tasks")
    assert listing.status_code == 200
    request_ids = {task["request_id"] for task in listing.json()["tasks"]}
    assert "LV-MOCK-SICK-PASS-001" in request_ids

    run = client.post("/leave-audit/tasks/LV-MOCK-SICK-PASS-001/run")
    assert run.status_code == 200
    assert run.json()["result"]["status"] == "PASS"

    detail = client.get("/leave-audit/tasks/LV-MOCK-SICK-PASS-001")
    assert detail.status_code == 200
    assert detail.json()["task"]["request_id"] == "LV-MOCK-SICK-PASS-001"
    assert detail.json()["result"]["verification_json"]["verify_status"] == "PASS"

    review = client.post(
        "/leave-audit/tasks/LV-MOCK-SICK-PASS-001/review",
        json={"decision": "REVIEW", "reviewer": "hr01", "comment": "抽检复核"},
    )
    assert review.status_code == 200
    assert review.json()["review"]["decision"] == "REVIEW"

    stats = client.get("/leave-audit/stats")
    assert stats.status_code == 200
    assert stats.json()["stats"]["REVIEW"] >= 1
