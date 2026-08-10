from __future__ import annotations

import json
from typing import Any

from id_doc_ocr.leave_audit.contracts.ocr import OcrResultEventV1
from id_doc_ocr.leave_audit.domain.aggregation import AttachmentDecisionInput, aggregate_attachment_decisions
from id_doc_ocr.leave_audit.domain.async_status import CallbackStatus, DecisionStatus, OcrJobStatus
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAuditResult
from id_doc_ocr.leave_audit.repository.base import LeaveAuditRepository
from id_doc_ocr.leave_audit.service.audit_service import _callback_payload_from_result, _leave_request_id_from_task
from id_doc_ocr.leave_audit.storage.base import ObjectStorage, sha256_hex
from id_doc_ocr.verification.rules import DEFAULT_FIELD_MAPPING_CONFIG, DEFAULT_RULE_CONFIGS, verify_attachment


class OcrResultConsumerService:
    """Leave Audit Service side of the OCR result contract.

    The database method commits consumed_message, result, decision and callback
    outbox before the RabbitMQ runtime acknowledges the event.
    """

    def __init__(self, repository: LeaveAuditRepository, storage: ObjectStorage, consumer_name: str = "leave-audit-result-v1") -> None:
        self.repository = repository
        self.storage = storage
        self.consumer_name = consumer_name

    def handle_event(self, event: OcrResultEventV1) -> bool:
        task = self.repository.get_task(event.request_id)
        if task is None:
            raise ValueError(f"task not found: {event.request_id}")
        if event.attachment_id not in {item.attachment_id for item in task.attachments}:
            raise ValueError("event attachment does not belong to task")

        if event.status == "FAILED":
            result = LeaveAuditResult(request_id=event.request_id, status=LeaveAuditStatus.ERROR,
                                      job_id=event.job_id, attachment_id=event.attachment_id,
                                      plugin_name=next((a.plugin_name for a in task.attachments if a.attachment_id == event.attachment_id), None),
                                      error_message=event.safe_error_message, ocr_status=OcrJobStatus.FAILED,
                                      callback_status=CallbackStatus.NOT_REQUIRED,
                                      ocr_profile_snapshot_id=event.ocr_profile_snapshot_id or task.ocr_profile_snapshot_id,
                                      decision_policy_snapshot_id=task.decision_policy_snapshot_id,
                                      field_mapping_snapshot_id=task.field_mapping_snapshot_id,
                                      callback_policy_snapshot_id=task.callback_policy_snapshot_id)
            return self.repository.apply_ocr_result(consumer_name=self.consumer_name, event_id=event.event_id, result=result)

        payload = self.storage.get_bytes(event.result_object_key or "")
        if sha256_hex(payload) != event.result_sha256:
            raise ValueError("OCR result SHA mismatch")
        document = json.loads(payload.decode("utf-8"))
        pages = document.get("pages") or []
        analysis = dict((pages[0].get("analysis") if pages and isinstance(pages[0], dict) else {}) or {})
        attachment = next(a for a in task.attachments if a.attachment_id == event.attachment_id)
        request = {"request_id": task.request_id, "leave_request_id": _leave_request_id_from_task(task),
                   "leave_type": task.leave_type, "applicant_name": task.employee_name,
                   "leave_start_date": task.leave_start_date, "leave_end_date": task.leave_end_date}
        request.update(dict(task.raw_payload.get("verification_context") or {}))
        mapping = dict(DEFAULT_FIELD_MAPPING_CONFIG)
        mapping.update(self.repository.get_field_mappings())
        rule = self.repository.get_rule_config(task.leave_type) or DEFAULT_RULE_CONFIGS.get(task.leave_type.upper())
        verification = verify_attachment(analysis, request, field_mapping_config=mapping, rule_config=rule)
        status = LeaveAuditStatus(str(verification.get("verify_status") or "REVIEW"))
        decision = {LeaveAuditStatus.PASS: DecisionStatus.PASS, LeaveAuditStatus.REVIEW: DecisionStatus.REVIEW_REQUIRED, LeaveAuditStatus.REJECT: DecisionStatus.REJECT}[status]
        result = LeaveAuditResult(request_id=event.request_id, status=status, plugin_name=attachment.plugin_name,
                                  analysis_json=analysis, verification_json=verification, job_id=event.job_id,
                                  attachment_id=event.attachment_id, ocr_status=OcrJobStatus.SUCCEEDED,
                                  decision_status=decision, callback_status=CallbackStatus.PENDING,
                                  ocr_profile_snapshot_id=event.ocr_profile_snapshot_id or task.ocr_profile_snapshot_id,
                                  decision_policy_snapshot_id=task.decision_policy_snapshot_id,
                                  field_mapping_snapshot_id=task.field_mapping_snapshot_id,
                                  callback_policy_snapshot_id=task.callback_policy_snapshot_id)
        callback_payload = _callback_payload_from_result(result)
        return self.repository.apply_ocr_result(consumer_name=self.consumer_name, event_id=event.event_id, result=result, callback_payload=callback_payload)


def aggregate_task_decision(results: list[LeaveAuditResult]) -> DecisionStatus:
    """Explicit adapter for callers that keep one result per attachment."""
    mapped = []
    for item in results:
        status = item.decision_status.value if item.decision_status else item.ocr_status.value
        mapped.append(AttachmentDecisionInput(item.attachment_id or item.request_id, status))
    return aggregate_attachment_decisions(mapped).decision_status
