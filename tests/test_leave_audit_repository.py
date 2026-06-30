from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAttachment, LeaveAuditResult, LeaveAuditTask, LeaveReviewDecision
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository


def test_repository_saves_and_queries_task_result_and_review(tmp_path):
    repo = SQLiteRepository(tmp_path / "leave_audit.db")
    task = LeaveAuditTask(
        request_id="LV-TEST-001",
        leave_type="SICK",
        employee_name="张三",
        attachments=[LeaveAttachment(attachment_id="A1", attachment_url="fixture://a.jpg")],
    )

    repo.save_task(task)
    loaded = repo.get_task("LV-TEST-001")
    assert loaded is not None
    assert loaded.employee_name == "张三"
    assert loaded.attachments[0].attachment_url == "fixture://a.jpg"

    result = LeaveAuditResult(request_id="LV-TEST-001", status=LeaveAuditStatus.PASS, verification_json={"verify_status": "PASS"})
    repo.save_result(result)
    assert repo.get_result("LV-TEST-001").status == LeaveAuditStatus.PASS

    repo.save_review(LeaveReviewDecision(request_id="LV-TEST-001", decision=LeaveAuditStatus.REVIEW, reviewer="hr01", comment="补充材料"))
    assert repo.get_task("LV-TEST-001").status == LeaveAuditStatus.REVIEW
    assert repo.list_reviews("LV-TEST-001")[0].reviewer == "hr01"


def test_repository_saves_prompt_configs_and_resolves_plugin_overrides(tmp_path):
    repo = SQLiteRepository(tmp_path / "leave_audit.db")

    repo.save_prompt_config("*", "field_extraction", "全局抽取提示")
    repo.save_prompt_config("diagnosis_proof", "field_extraction", "诊断证明抽取提示")
    repo.save_prompt_config("diagnosis_proof", "verification", "诊断证明审核提示")
    repo.save_prompt_config("diagnosis_proof", "qa_assistant", "禁用问答提示", enabled=False)

    configs = repo.get_prompt_configs()
    assert {item["prompt_type"] for item in configs} == {"field_extraction", "verification", "qa_assistant"}
    assert repo.get_effective_prompt_texts("diagnosis_proof") == {
        "field_extraction": "诊断证明抽取提示",
        "verification": "诊断证明审核提示",
    }
    assert repo.get_effective_prompt_texts("marriage_certificate") == {"field_extraction": "全局抽取提示"}
