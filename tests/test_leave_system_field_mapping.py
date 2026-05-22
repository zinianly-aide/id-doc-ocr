import json

import pytest

from id_doc_ocr.leave_audit.adapters import field_mapping
from id_doc_ocr.leave_audit.adapters.field_mapping import normalize_pending_item, resolve_field


def test_builtin_mapping_resolves_camel_case_fields(monkeypatch):
    monkeypatch.delenv("ID_DOC_OCR_LEAVE_SYSTEM_FIELD_MAPPING_FILE", raising=False)
    payload = {
        "leaveRequestId": "LR-CAMEL-001",
        "employeeId": "E001",
        "employeeName": "张三",
        "leaveType": "SICK",
        "leaveStartDate": "2026-06-01",
        "leaveEndDate": "2026-06-03",
        "attachments": [
            {
                "attachmentId": "ATT-CAMEL-001",
                "attachmentName": "diagnosis.jpg",
                "attachmentUrl": "file-camel-001",
                "pluginName": "diagnosis_proof",
            }
        ],
    }

    normalized = normalize_pending_item(payload)

    assert resolve_field(payload, "leave_request_id") == "LR-CAMEL-001"
    assert normalized["leave_request_id"] == "LR-CAMEL-001"
    assert normalized["employee_id"] == "E001"
    assert normalized["employee_name"] == "张三"
    assert normalized["leave_type"] == "SICK"
    assert normalized["attachments"][0]["attachment_id"] == "ATT-CAMEL-001"
    assert normalized["attachments"][0]["attachment_name"] == "diagnosis.jpg"
    assert normalized["attachments"][0]["attachment_url"] == "file-camel-001"
    assert normalized["attachments"][0]["plugin_name"] == "diagnosis_proof"


def test_builtin_mapping_resolves_real_system_style_fields(monkeypatch):
    monkeypatch.delenv("ID_DOC_OCR_LEAVE_SYSTEM_FIELD_MAPPING_FILE", raising=False)
    payload = {
        "applyNo": "LR-REAL-001",
        "empNo": "E002",
        "empName": "李四",
        "absenceType": "MARRIAGE",
        "startTime": "2026-06-10 09:00:00",
        "endTime": "2026-06-12 18:00:00",
        "attachments": [
            {
                "fileId": "FILE-001",
                "fileName": "marriage.jpg",
                "fileUrl": "https://leave.example.test/files/FILE-001",
            }
        ],
    }

    normalized = normalize_pending_item(payload)

    assert normalized["leave_request_id"] == "LR-REAL-001"
    assert normalized["employee_id"] == "E002"
    assert normalized["employee_name"] == "李四"
    assert normalized["leave_type"] == "MARRIAGE"
    assert normalized["leave_start_date"] == "2026-06-10 09:00:00"
    assert normalized["leave_end_date"] == "2026-06-12 18:00:00"
    assert normalized["attachments"][0]["attachment_id"] == "FILE-001"
    assert normalized["attachments"][0]["attachment_name"] == "marriage.jpg"
    assert normalized["attachments"][0]["attachment_url"] == "https://leave.example.test/files/FILE-001"


def test_external_json_mapping_file_can_add_aliases(tmp_path, monkeypatch):
    mapping_file = tmp_path / "field_mapping.json"
    mapping_file.write_text(
        json.dumps(
            {
                "leave_request_id": ["externalApplyCode"],
                "employee_name": ["personDisplayName"],
                "attachment_url": ["downloadLink"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_SYSTEM_FIELD_MAPPING_FILE", str(mapping_file))

    payload = {
        "externalApplyCode": "LR-CONFIG-001",
        "employeeId": "E003",
        "personDisplayName": "王五",
        "leaveType": "SICK",
        "attachments": [
            {
                "attachmentId": "ATT-CONFIG-001",
                "fileName": "diagnosis.jpg",
                "downloadLink": "configured-url",
            }
        ],
    }

    normalized = normalize_pending_item(payload)

    assert normalized["leave_request_id"] == "LR-CONFIG-001"
    assert normalized["employee_name"] == "王五"
    assert normalized["attachments"][0]["attachment_url"] == "configured-url"


def test_external_yaml_mapping_file_can_add_aliases(tmp_path, monkeypatch):
    mapping_file = tmp_path / "field_mapping.yaml"
    mapping_file.write_text(
        "leave_request_id:\n"
        "  - customApplyNo\n"
        "employee_name:\n"
        "  - customEmployeeName\n"
        "attachment_url:\n"
        "  - customFileUrl\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_SYSTEM_FIELD_MAPPING_FILE", str(mapping_file))

    payload = {
        "customApplyNo": "LR-YAML-001",
        "customEmployeeName": "赵六",
        "leaveType": "SICK",
        "attachments": [{"attachmentId": "ATT-YAML-001", "fileName": "a.jpg", "customFileUrl": "yaml-url"}],
    }

    normalized = normalize_pending_item(payload)

    assert normalized["leave_request_id"] == "LR-YAML-001"
    assert normalized["employee_name"] == "赵六"
    assert normalized["attachments"][0]["attachment_url"] == "yaml-url"


def test_missing_required_fields_raise_clear_error(monkeypatch):
    monkeypatch.delenv("ID_DOC_OCR_LEAVE_SYSTEM_FIELD_MAPPING_FILE", raising=False)

    with pytest.raises(ValueError, match="missing required field 'leave_type'"):
        normalize_pending_item({"leaveRequestId": "LR-MISSING-001", "employeeName": "张三", "attachments": []})

    with pytest.raises(ValueError, match="missing required attachment field 'attachment_url'"):
        normalize_pending_item(
            {
                "leaveRequestId": "LR-MISSING-002",
                "employeeName": "张三",
                "leaveType": "SICK",
                "attachments": [{"attachmentId": "ATT-MISSING-001"}],
            }
        )
