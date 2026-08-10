from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from id_doc_ocr.leave_audit.contracts.ocr import OcrCommandV1, OcrResultEventV1


def _sha(char: str = "a") -> str:
    return char * 64


def test_ocr_command_contains_transport_safe_metadata_only():
    command = OcrCommandV1(
        command_id="cmd-1",
        job_id="job-1",
        request_id="LV-1",
        attachment_id="att-1",
        object_key="attachments/att-1.pdf",
        content_sha256=_sha(),
        plugin_name="diagnosis_proof",
        pipeline_profile="production-v1",
        ocr_profile_snapshot_id="ocr-cfg-1",
        trace_id="trace-1",
        created_at=datetime.now(timezone.utc),
    )

    payload = command.model_dump()
    assert payload["schema_version"] == "1.0"
    assert "decision_policy_snapshot_id" not in payload
    assert "raw_ocr_text" not in payload


def test_ocr_command_rejects_invalid_sha256():
    with pytest.raises(ValidationError, match="content_sha256"):
        OcrCommandV1(
            command_id="cmd-1",
            job_id="job-1",
            request_id="LV-1",
            attachment_id="att-1",
            object_key="attachments/att-1.pdf",
            content_sha256="not-a-sha",
            plugin_name="diagnosis_proof",
            pipeline_profile="production-v1",
            ocr_profile_snapshot_id="ocr-cfg-1",
            trace_id="trace-1",
            created_at=datetime.now(timezone.utc),
        )


def test_failed_event_requires_safe_classified_error():
    with pytest.raises(ValidationError, match="error_category"):
        OcrResultEventV1(
            event_id="event-1",
            causation_id="cmd-1",
            job_id="job-1",
            request_id="LV-1",
            attachment_id="att-1",
            status="FAILED",
            engine_version="mock-1",
            pipeline_profile="production-v1",
            ocr_profile_snapshot_id="ocr-cfg-1",
            trace_id="trace-1",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )


def test_success_event_references_large_result_in_object_storage():
    event = OcrResultEventV1(
        event_id="event-1",
        causation_id="cmd-1",
        job_id="job-1",
        request_id="LV-1",
        attachment_id="att-1",
        status="SUCCEEDED",
        result_object_key="ocr-results/job-1.json",
        result_sha256=_sha("b"),
        page_count=2,
        engine_version="mock-1",
        pipeline_profile="production-v1",
        ocr_profile_snapshot_id="ocr-cfg-1",
        trace_id="trace-1",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    assert event.result_object_key == "ocr-results/job-1.json"
    assert event.result_sha256 == _sha("b")

