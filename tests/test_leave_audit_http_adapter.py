import json

import httpx
import pytest

from id_doc_ocr.leave_audit.adapters.http_leave_system import (
    HttpLeaveSystemAdapter,
    HttpLeaveSystemSettings,
    LeaveSystemHttpError,
)
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAuditResult


def build_adapter(handler):
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    settings = HttpLeaveSystemSettings(
        base_url="https://leave.example.test",
        token="secret-token",
        pending_api="/api/pending",
        download_api="/api/download",
        callback_api="/api/callback",
        timeout_seconds=3,
    )
    return HttpLeaveSystemAdapter(settings=settings, client=client)


def test_fetch_pending_attachments_parses_http_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/pending"
        assert request.headers["authorization"] == "Bearer secret-token"
        return httpx.Response(
            200,
            json={
                "tasks": [
                    {
                        "request_id": "LV-HTTP-001",
                        "leave_request_id": "LR-001",
                        "leave_type": "SICK",
                        "employee_id": "E001",
                        "employee_name": "张三",
                        "leave_start_date": "2026-04-01",
                        "leave_end_date": "2026-04-03",
                        "attachments": [
                            {
                                "attachment_id": "ATT-001",
                                "attachment_url": "file-001",
                                "filename": "diagnosis.jpg",
                                "content_type": "image/jpeg",
                                "plugin_name": "diagnosis_proof",
                            }
                        ],
                    }
                ]
            },
        )

    adapter = build_adapter(handler)

    tasks = adapter.fetch_pending_attachments()

    assert len(tasks) == 1
    assert tasks[0].request_id == "LV-HTTP-001"
    assert tasks[0].raw_payload["leave_request_id"] == "LR-001"
    assert tasks[0].attachments[0].filename == "diagnosis.jpg"


def test_download_attachment_returns_bytes():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/download"
        assert request.url.params["attachment_url"] == "file-001"
        return httpx.Response(200, content=b"image-bytes")

    adapter = build_adapter(handler)

    assert adapter.download_attachment("file-001") == b"image-bytes"


def test_push_audit_result_sends_callback_payload():
    seen_payload = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/callback"
        seen_payload.update(json.loads(request.content.decode("utf-8")))
        return httpx.Response(204)

    adapter = build_adapter(handler)
    result = LeaveAuditResult(
        request_id="LV-HTTP-001",
        status=LeaveAuditStatus.REVIEW,
        verification_json={
            "verify_status": "REVIEW",
            "risk_level": "MEDIUM",
            "risk_score": 45,
            "needs_manual_review": True,
            "summary_message": "REVIEW: needs HR review",
            "rule_results": [{"rule_code": "applicant_name_match", "passed": False}],
            "evidence": {"request": {"leave_request_id": "LR-001"}},
        },
    )

    adapter.push_audit_result(result)

    assert seen_payload == {
        "request_id": "LV-HTTP-001",
        "leave_request_id": "LR-001",
        "verify_status": "REVIEW",
        "risk_level": "MEDIUM",
        "risk_score": 45,
        "needs_manual_review": True,
        "summary": "REVIEW: needs HR review",
        "rule_results": [{"rule_code": "applicant_name_match", "passed": False}],
    }


def test_http_non_2xx_raises_clear_exception():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream unavailable")

    adapter = build_adapter(handler)

    with pytest.raises(LeaveSystemHttpError, match="status=503"):
        adapter.fetch_pending_attachments()
