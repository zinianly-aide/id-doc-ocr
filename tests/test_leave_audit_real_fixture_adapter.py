from __future__ import annotations

import json

import pytest

from id_doc_ocr.leave_audit.adapters.mock_leave_system import MockLeaveSystemAdapter


def test_fixture_url_without_fixture_dir_keeps_mock_bytes(monkeypatch):
    monkeypatch.delenv("ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR", raising=False)
    adapter = MockLeaveSystemAdapter()

    payload = adapter.download_attachment("fixture://sick-pass.jpg")

    assert payload == b"mock-image-bytes:fixture://sick-pass.jpg"


def test_fixture_url_with_fixture_dir_reads_real_file_bytes(tmp_path, monkeypatch):
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    image_file = fixture_dir / "sick-pass.jpg"
    image_file.write_bytes(b"real-image-bytes")
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR", str(fixture_dir))

    adapter = MockLeaveSystemAdapter()

    assert adapter.download_attachment("fixture://sick-pass.jpg") == b"real-image-bytes"


def test_fixture_url_with_fixture_dir_reports_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR", str(tmp_path))
    adapter = MockLeaveSystemAdapter()

    with pytest.raises(FileNotFoundError, match="fixture://missing.jpg"):
        adapter.download_attachment("fixture://missing.jpg")


def test_fixture_url_with_fixture_dir_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR", str(tmp_path))
    adapter = MockLeaveSystemAdapter()

    with pytest.raises(ValueError, match="path traversal"):
        adapter.download_attachment("fixture://../secret.jpg")


def test_fixture_file_env_switches_task_file(tmp_path, monkeypatch):
    task_file = tmp_path / "custom_tasks.json"
    task_file.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "request_id": "sick-real-ocr-review-001",
                        "leave_type": "SICK",
                        "employee_id": "E100",
                        "employee_name": "张三",
                        "attachments": [
                            {
                                "attachment_id": "ATT-REAL-001",
                                "attachment_url": "fixture://sick-diagnosis-proof.jpg",
                                "filename": "sick-diagnosis-proof.jpg",
                                "content_type": "image/jpeg",
                                "plugin_name": "diagnosis_proof",
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_FILE", str(task_file))

    adapter = MockLeaveSystemAdapter()
    tasks = adapter.fetch_pending_attachments()

    assert [task.request_id for task in tasks] == ["sick-real-ocr-review-001"]
    assert tasks[0].attachments[0].attachment_url == "fixture://sick-diagnosis-proof.jpg"
