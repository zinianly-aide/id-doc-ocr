from id_doc_ocr.application.inference_service import InferenceServiceSettings
from id_doc_ocr.leave_audit.adapters.mock_leave_system import MockLeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.leave_audit.service.audit_service import AuditService
from id_doc_ocr.leave_audit.service.task_service import TaskService
from id_doc_ocr.application.inference_service import InferenceService
from id_doc_ocr.leave_audit.domain.models import LeaveAttachment, LeaveAuditTask
from id_doc_ocr.utils.document_pages import DocumentPage


def test_audit_service_processes_mock_tasks_to_pass_review_reject(tmp_path):
    repo = SQLiteRepository(tmp_path / "leave_audit.db")
    adapter = MockLeaveSystemAdapter()
    TaskService(repo, adapter).sync_pending()
    service = AuditService(repo, adapter, InferenceService(InferenceServiceSettings()))

    statuses = {task.request_id: service.run_task(task.request_id).status for task in repo.list_tasks()}

    assert statuses["LV-MOCK-SICK-PASS-001"] == LeaveAuditStatus.PASS
    assert statuses["LV-MOCK-SICK-REVIEW-001"] == LeaveAuditStatus.REVIEW
    assert statuses["LV-MOCK-SICK-REJECT-001"] == LeaveAuditStatus.REJECT
    result = repo.get_result("LV-MOCK-SICK-PASS-001")
    assert result.analysis_json
    assert result.verification_json["autoPassReadiness"]["status"] == "ready"


class _PdfAttachmentAdapter:
    def fetch_pending_attachments(self):
        return []

    def download_attachment(self, attachment_url: str) -> bytes:
        assert attachment_url == "oracle-tna://DOC-PDF-001"
        return b"%PDF-1.7\nfake"

    def push_audit_result(self, result):
        pass


class _MultiPageInferenceService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["image"] == b"page-1":
            fields = {"patient_name": "张三"}
        elif kwargs["image"] == b"page-2":
            fields = {
                "rest_start_date": "2026-04-01",
                "rest_end_date": "2026-04-03",
                "issue_date": "2026-04-01",
            }
        else:
            raise AssertionError(f"unexpected image bytes: {kwargs['image']!r}")
        return {"analysis": _analysis(fields)}


def _analysis(fields: dict) -> dict:
    return {
        "doc_type": "diagnosis_proof",
        "classification_evidence": {
            "attachment_label": "MEDICAL_CERTIFICATE",
            "attachment_confidence": 0.9,
            "matched_keywords": ["MEDICAL_CERTIFICATE"],
        },
        "extracted_fields": [
            {"name": key, "value": value, "confidence": 0.95, "source": "parsed_field", "bbox": None, "evidence_text": None, "matched": False}
            for key, value in fields.items()
        ],
        "risk": {
            "score": 0.0,
            "review_action": "accept_with_warning",
            "review_recommended": False,
            "quality_passed": True,
            "validation_accepted": True,
        },
        "review": {"warnings": [], "evidence": {"fields": []}},
        "validation": {"accepted": True, "issues": []},
        "raw_artifacts": {},
    }


def test_audit_service_processes_multipage_pdf_attachment_from_database_binary(tmp_path, monkeypatch):
    repo = SQLiteRepository(tmp_path / "leave_audit.db")
    task = LeaveAuditTask(
        request_id="LV-PDF-001",
        leave_type="SICK",
        employee_name="张三",
        leave_start_date="2026-04-01",
        leave_end_date="2026-04-03",
        attachments=[
            LeaveAttachment(
                attachment_id="ATT-PDF-001",
                attachment_url="oracle-tna://DOC-PDF-001",
                filename="diagnosis.pdf",
                content_type="application/pdf",
                plugin_name="diagnosis_proof",
            )
        ],
    )
    repo.save_task(task)
    repo.save_prompt_config("diagnosis_proof", "field_extraction", "请抽取患者姓名和病假起止日期")
    repo.save_prompt_config("diagnosis_proof", "verification", "病假日期必须覆盖请假日期")

    def fake_expand_document_pages(content, *, filename=None, content_type=None):
        assert content == b"%PDF-1.7\nfake"
        assert filename == "diagnosis.pdf"
        assert content_type == "application/pdf"
        return [
            DocumentPage(content=b"page-1", page_number=1, page_count=2, filename="diagnosis-page-1.png", content_type="image/png", document_kind="pdf", source_filename=filename),
            DocumentPage(content=b"page-2", page_number=2, page_count=2, filename="diagnosis-page-2.png", content_type="image/png", document_kind="pdf", source_filename=filename),
        ]

    monkeypatch.setattr("id_doc_ocr.leave_audit.service.audit_service.expand_document_pages", fake_expand_document_pages)
    inference = _MultiPageInferenceService()
    service = AuditService(repo, _PdfAttachmentAdapter(), inference)

    result = service.run_task("LV-PDF-001")

    assert result.status == LeaveAuditStatus.PASS
    assert [call["filename"] for call in inference.calls] == ["diagnosis-page-1.png", "diagnosis-page-2.png"]
    assert all(call["prompt_context"]["custom_prompt"] == "请抽取患者姓名和病假起止日期" for call in inference.calls)
    assert all(call["prompt_context"]["verification_prompt"] == "病假日期必须覆盖请假日期" for call in inference.calls)
    assert result.verification_json["verify_status"] == "PASS"
    assert result.verification_json["extracted_fields"]["patient_name"] == "张三"
    assert result.verification_json["extracted_fields"]["rest_start_date"] == "2026-04-01"
    assert result.analysis_json["document"]["document_kind"] == "pdf"
    assert result.analysis_json["document"]["page_count"] == 2
    assert result.analysis_json["raw_artifacts"]["prompt_context"]["prompt_texts"] == {
        "field_extraction": "请抽取患者姓名和病假起止日期",
        "verification": "病假日期必须覆盖请假日期",
    }
    assert {field["name"]: field["document_page"] for field in result.analysis_json["extracted_fields"]} == {
        "patient_name": 1,
        "rest_start_date": 2,
        "rest_end_date": 2,
        "issue_date": 2,
    }


def test_audit_service_uses_rule_prompt_text_as_field_extraction_fallback(tmp_path, monkeypatch):
    repo = SQLiteRepository(tmp_path / "leave_audit.db")
    task = LeaveAuditTask(
        request_id="LV-PROMPT-FALLBACK-001",
        leave_type="SICK",
        employee_name="张三",
        attachments=[
            LeaveAttachment(
                attachment_id="ATT-PROMPT-001",
                attachment_url="oracle-tna://DOC-PDF-001",
                filename="diagnosis.jpg",
                content_type="image/jpeg",
                plugin_name="diagnosis_proof",
            )
        ],
    )
    repo.save_task(task)
    repo.save_rule_config("SICK", "旧配置提示词也要生效", [], enabled=True)
    monkeypatch.setattr(
        "id_doc_ocr.leave_audit.service.audit_service.expand_document_pages",
        lambda content, *, filename=None, content_type=None: [
            DocumentPage(content=b"page-1", page_number=1, page_count=1, filename="diagnosis.jpg", content_type="image/jpeg")
        ],
    )
    inference = _MultiPageInferenceService()
    service = AuditService(repo, _PdfAttachmentAdapter(), inference)

    result = service.run_task("LV-PROMPT-FALLBACK-001")

    assert result.status == LeaveAuditStatus.REVIEW
    assert inference.calls[0]["prompt_context"]["custom_prompt"] == "旧配置提示词也要生效"
    assert inference.calls[0]["prompt_context"]["verification_prompt"] == "旧配置提示词也要生效"
