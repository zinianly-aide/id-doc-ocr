from pathlib import Path
import json
import sqlite3

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


def test_leave_audit_async_run_returns_202_and_outboxes(tmp_path, monkeypatch):
    monkeypatch.setenv("ID_DOC_OCR_EXECUTION_MODE", "async")
    monkeypatch.setenv("ID_DOC_OCR_OBJECT_STORAGE_ROOT", str(tmp_path / "objects"))
    client = build_client(tmp_path)
    assert client.post("/leave-audit/sync").status_code == 200
    response = client.post("/leave-audit/tasks/LV-MOCK-SICK-PASS-001/run")
    assert response.status_code == 202
    assert response.json()["status"] == "QUEUED"
    detail = client.get("/leave-audit/tasks/LV-MOCK-SICK-PASS-001").json()["task"]
    assert detail["ocr_status"] == "QUEUED"
    repository = client.app.state.leave_audit_repository
    assert len(repository.list_pending_outbox()) == 1
    with repository.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM leave_audit_ocr_job").fetchone()[0] == 1


def test_leave_audit_dify_run_requires_config_without_mutating_task(tmp_path, monkeypatch):
    monkeypatch.delenv("ID_DOC_OCR_DIFY_API_KEY", raising=False)
    monkeypatch.delenv("DIFY_API_KEY", raising=False)
    client = build_client(tmp_path)

    sync = client.post("/leave-audit/sync")
    assert sync.status_code == 200

    run = client.post("/leave-audit/tasks/LV-MOCK-SICK-PASS-001/run?field_parser_backend=dify")
    assert run.status_code == 422
    assert "Dify parser is not configured" in run.json()["detail"]

    detail = client.get("/leave-audit/tasks/LV-MOCK-SICK-PASS-001")
    assert detail.status_code == 200
    assert detail.json()["task"]["status"] == "PULLED"
    assert detail.json()["result"] is None


def test_leave_audit_config_api(tmp_path):
    client = build_client(tmp_path)

    config = client.get("/leave-audit/config")
    assert config.status_code == 200
    assert any(item["canonical_field"] == "applicant_name" for item in config.json()["field_mappings"])
    assert "field_mapping" in config.json()["guidance"]
    assert "prompt_config" in config.json()["guidance"]
    assert config.json()["prompt_configs"] == []

    update_mapping = client.put(
        "/leave-audit/config/field-mappings",
        json={"mappings": [{"canonical_field": "applicant_name", "candidates": ["name", "patient_name"]}]},
    )
    assert update_mapping.status_code == 200
    applicant_mapping = next(item for item in update_mapping.json()["field_mappings"] if item["canonical_field"] == "applicant_name")
    assert applicant_mapping["candidates"] == ["name", "patient_name"]

    update_rules = client.put(
        "/leave-audit/config/rules",
        json={
            "configs": [
                {
                    "leave_type": "MARRIAGE",
                    "prompt_text": "婚假核验",
                    "enabled": True,
                    "rules": [{"type": "required_name", "rule_code": "must_have_name", "on_fail": "REJECT"}],
                }
            ]
        },
    )
    assert update_rules.status_code == 200
    marriage_config = next(item for item in update_rules.json()["rule_configs"] if item["leave_type"] == "MARRIAGE")
    assert marriage_config["prompt_text"] == "婚假核验"

    update_prompts = client.put(
        "/leave-audit/config/prompts",
        json={
            "configs": [
                {
                    "recognition_type": "diagnosis_proof",
                    "prompt_type": "field_extraction",
                    "prompt_text": "只抽取病假证明字段",
                    "enabled": True,
                }
            ]
        },
    )
    assert update_prompts.status_code == 200
    assert update_prompts.json()["prompt_configs"][0]["recognition_type"] == "diagnosis_proof"
    assert update_prompts.json()["prompt_configs"][0]["prompt_type"] == "field_extraction"
    assert update_prompts.json()["prompt_configs"][0]["prompt_text"] == "只抽取病假证明字段"


def test_leave_audit_sync_from_oracle_tna_sqlite_source(tmp_path, monkeypatch):
    source_db = tmp_path / "oracle_tna.db"
    payload = {
        "request_id": "LV-TNA-001",
        "leave_type": "SICK",
        "employee_id": "E001",
        "employee_name": "张三",
        "leave_start_date": "2026-04-01",
        "leave_end_date": "2026-04-03",
        "attachments": [
            {
                "attachment_id": "ATT-TNA-001",
                "attachment_url": "./testfile/test1.png",
                "filename": "sick-pass.jpg",
                "content_type": "image/jpeg",
                "plugin_name": "diagnosis_proof",
                "metadata": {},
            }
        ],
    }
    with sqlite3.connect(source_db) as conn:
        conn.execute("CREATE TABLE tna_leave_audit_task (payload_json TEXT NOT NULL)")
        conn.execute("INSERT INTO tna_leave_audit_task (payload_json) VALUES (?)", (json.dumps(payload, ensure_ascii=False),))

    monkeypatch.setenv("ID_DOC_OCR_ORACLE_TNA_DB", str(source_db))
    client = build_client(tmp_path)
    sync = client.post("/leave-audit/sync")
    assert sync.status_code == 200
    assert sync.json()["tasks"][0]["request_id"] == "LV-TNA-001"

    detail = client.get("/leave-audit/tasks/LV-TNA-001")
    assert detail.status_code == 200
    assert detail.json()["task"]["employee_id"] == "E001"
    assert detail.json()["task"]["attachments"][0] == {
        "attachment_id": "ATT-TNA-001",
        "attachment_url": "./testfile/test1.png",
        "filename": "sick-pass.jpg",
        "content_type": "image/jpeg",
        "plugin_name": "diagnosis_proof",
        "metadata": {},
    }
