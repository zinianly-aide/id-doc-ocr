from id_doc_ocr.application.inference_service import InferenceServiceSettings
from id_doc_ocr.leave_audit.adapters.mock_leave_system import MockLeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.leave_audit.service.audit_service import AuditService
from id_doc_ocr.leave_audit.service.task_service import TaskService
from id_doc_ocr.application.inference_service import InferenceService


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
