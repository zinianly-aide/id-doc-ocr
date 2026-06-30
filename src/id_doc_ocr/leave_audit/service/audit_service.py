from __future__ import annotations

import logging
import os
import time
from typing import Any

from id_doc_ocr.application.inference_service import InferenceService
from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.mapping import LEAVE_TYPE_PLUGIN_MAPPING, resolve_plugin_for_leave_task
from id_doc_ocr.leave_audit.domain.models import LeaveAttachment, LeaveAuditResult, LeaveAuditTask
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.parsers.dify_field_parser import dify_configuration_message, is_dify_configured
from id_doc_ocr.utils.document_pages import DocumentPage, expand_document_pages
from id_doc_ocr.verification.rules import DEFAULT_FIELD_MAPPING_CONFIG, DEFAULT_RULE_CONFIGS, verify_attachment

logger = logging.getLogger(__name__)


def is_leave_audit_dry_run() -> bool:
    return str(os.getenv("ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN", "false")).strip().lower() in {"1", "true", "yes", "on"}


def _adapter_type(adapter: LeaveSystemAdapter) -> str:
    return adapter.__class__.__name__


def _leave_request_id_from_task(task: LeaveAuditTask) -> str:
    return str(task.raw_payload.get("leave_request_id") or task.raw_payload.get("request_id") or task.request_id)


def _callback_payload_from_result(result: LeaveAuditResult) -> dict[str, Any]:
    verification = result.verification_json or {}
    evidence = verification.get("evidence") if isinstance(verification.get("evidence"), dict) else {}
    request_evidence = (evidence or {}).get("request") or {}
    return {
        "request_id": result.request_id,
        "leave_request_id": request_evidence.get("leave_request_id") or request_evidence.get("request_id") or result.request_id,
        "verify_status": verification.get("verify_status") or result.status.value,
        "risk_level": verification.get("risk_level"),
        "risk_score": verification.get("risk_score"),
        "needs_manual_review": verification.get("needs_manual_review", result.status != LeaveAuditStatus.PASS),
        "summary": verification.get("summary_message") or result.error_message,
        "rule_results": verification.get("rule_results") or [],
    }


def _attachment_filename(attachment_id: str, filename: str | None, content_type: str | None) -> str:
    if filename:
        return filename
    if str(content_type or "").split(";", 1)[0].strip().lower() in {"application/pdf", "application/x-pdf"}:
        return f"{attachment_id}.pdf"
    return f"{attachment_id}.jpg"


def _non_empty(value: Any) -> bool:
    return value not in (None, "", [])


def _field_score(field: dict[str, Any]) -> tuple[int, float]:
    confidence = field.get("confidence")
    try:
        confidence_score = float(confidence) if confidence is not None else 0.0
    except (TypeError, ValueError):
        confidence_score = 0.0
    return (1 if _non_empty(field.get("value")) else 0, confidence_score)


def _merge_extracted_fields(page_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for run in page_runs:
        page: DocumentPage = run["page"]
        analysis = run["analysis"]
        for raw_field in analysis.get("extracted_fields") or []:
            if not isinstance(raw_field, dict) or not raw_field.get("name"):
                continue
            field = dict(raw_field)
            field["document_page"] = page.page_number
            field.setdefault("source_document", page.source_filename)
            name = str(field["name"])
            existing = merged.get(name)
            if existing is None or _field_score(field) > _field_score(existing):
                merged[name] = field
    return list(merged.values())


def _best_classification(page_runs: list[dict[str, Any]]) -> dict[str, Any]:
    best: dict[str, Any] = {}
    best_score = (-1, -1.0)
    for run in page_runs:
        page: DocumentPage = run["page"]
        classification = dict((run["analysis"].get("classification_evidence") or {}))
        label = str(classification.get("attachment_label") or "UNKNOWN")
        try:
            confidence = float(classification.get("attachment_confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        score = (0 if label == "UNKNOWN" else 1, confidence)
        if score > best_score:
            best = classification
            best["document_page"] = page.page_number
            best_score = score
    return best


def _merge_validation(page_runs: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    accepted = True
    for run in page_runs:
        page: DocumentPage = run["page"]
        validation = run["analysis"].get("validation") or {}
        accepted = accepted and bool(validation.get("accepted", True))
        for raw_issue in validation.get("issues") or []:
            if isinstance(raw_issue, dict):
                issue = dict(raw_issue)
                issue["document_page"] = page.page_number
                issues.append(issue)
    return {"accepted": accepted, "issues": issues}


def _merge_risk(page_runs: list[dict[str, Any]]) -> dict[str, Any]:
    action_rank = {"accept": 0, "accept_with_warning": 1, "review": 2, "reject": 3}
    merged = {
        "score": 0.0,
        "review_action": "accept_with_warning",
        "review_recommended": False,
        "quality_passed": True,
        "validation_accepted": True,
    }
    best_action_rank = action_rank[merged["review_action"]]
    for run in page_runs:
        risk = run["analysis"].get("risk") or {}
        try:
            merged["score"] = max(float(merged["score"]), float(risk.get("score") or 0.0))
        except (TypeError, ValueError):
            pass
        action = str(risk.get("review_action") or "")
        if action_rank.get(action, -1) > best_action_rank:
            merged["review_action"] = action
            best_action_rank = action_rank[action]
        merged["review_recommended"] = bool(merged["review_recommended"] or risk.get("review_recommended"))
        merged["quality_passed"] = bool(merged["quality_passed"] and risk.get("quality_passed", True))
        merged["validation_accepted"] = bool(merged["validation_accepted"] and risk.get("validation_accepted", True))
    return merged


def _page_summary(page: DocumentPage, analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_number": page.page_number,
        "page_count": page.page_count,
        "filename": page.filename,
        "content_type": page.content_type,
        "document_kind": page.document_kind,
        "doc_type": analysis.get("doc_type"),
        "classification_evidence": analysis.get("classification_evidence") or {},
        "extracted_fields": analysis.get("extracted_fields") or [],
        "validation": analysis.get("validation") or {},
        "risk": analysis.get("risk") or {},
    }


def _merge_page_analyses(
    *,
    plugin_name: str,
    attachment_id: str,
    source_filename: str | None,
    source_content_type: str | None,
    page_runs: list[dict[str, Any]],
) -> dict[str, Any]:
    if len(page_runs) == 1 and page_runs[0]["page"].document_kind != "pdf":
        return page_runs[0]["analysis"]

    first_analysis = dict(page_runs[0]["analysis"])
    pages = [_page_summary(run["page"], run["analysis"]) for run in page_runs]
    raw_artifacts = dict(first_analysis.get("raw_artifacts") or {})
    raw_artifacts["document_pages"] = pages
    raw_artifacts["page_count"] = len(page_runs)

    first_analysis.update(
        {
            "doc_type": plugin_name,
            "classification_evidence": _best_classification(page_runs),
            "extracted_fields": _merge_extracted_fields(page_runs),
            "validation": _merge_validation(page_runs),
            "risk": _merge_risk(page_runs),
            "raw_artifacts": raw_artifacts,
            "document": {
                "attachment_id": attachment_id,
                "source_filename": source_filename,
                "source_content_type": source_content_type,
                "document_kind": page_runs[0]["page"].document_kind,
                "page_count": len(page_runs),
            },
            "document_pages": pages,
        }
    )
    return first_analysis


def _prompt_context(
    *,
    repository: SQLiteRepository,
    plugin_name: str,
    task: LeaveAuditTask,
    rule_config: dict[str, Any] | None,
) -> dict[str, Any]:
    prompt_texts = repository.get_effective_prompt_texts(plugin_name)
    legacy_prompt = str((rule_config or {}).get("prompt_text") or "").strip()
    if legacy_prompt:
        prompt_texts.setdefault("field_extraction", legacy_prompt)
        prompt_texts.setdefault("verification", legacy_prompt)
    return {
        "recognition_type": plugin_name,
        "leave_type": task.leave_type,
        "prompt_texts": prompt_texts,
        "custom_prompt": prompt_texts.get("field_extraction", ""),
        "verification_prompt": prompt_texts.get("verification", ""),
    }


def _plugin_for_attachment(task: LeaveAuditTask, attachment: LeaveAttachment) -> str:
    explicit = attachment.plugin_name or attachment.metadata.get("plugin_name")
    if explicit:
        return str(explicit)
    leave_type = str(task.leave_type or "").upper()
    return LEAVE_TYPE_PLUGIN_MAPPING.get(leave_type, "diagnosis_proof")


def _status_rank(status: LeaveAuditStatus) -> int:
    ranks = {
        LeaveAuditStatus.PASS: 0,
        LeaveAuditStatus.REVIEW: 1,
        LeaveAuditStatus.REJECT: 2,
        LeaveAuditStatus.ERROR: 3,
    }
    return ranks.get(status, 4)


def _attachment_result_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "attachment_id": result.get("attachment_id"),
        "filename": result.get("filename"),
        "content_type": result.get("content_type"),
        "plugin_name": result.get("plugin_name"),
        "status": result.get("status"),
        "verify_status": (result.get("verification_json") or {}).get("verify_status"),
        "matched_attachment_type": (result.get("verification_json") or {}).get("matched_attachment_type"),
        "risk_level": (result.get("verification_json") or {}).get("risk_level"),
        "error_message": result.get("error_message"),
    }


def _log_audit_event(**fields: Any) -> None:
    details = " ".join(f"{key}={value}" for key, value in fields.items() if value is not None)
    logger.info("leave_audit_event %s", details)


class AuditService:
    def __init__(self, repository: SQLiteRepository, adapter: LeaveSystemAdapter, inference_service: InferenceService | None = None) -> None:
        self.repository = repository
        self.adapter = adapter
        self.inference_service = inference_service or InferenceService()

    def run_task(self, request_id: str, field_parser_backend: str | None = None) -> LeaveAuditResult:
        task = self.repository.get_task(request_id)
        if task is None:
            raise KeyError(f"Leave audit task not found: {request_id}")
        if field_parser_backend == "dify":
            plugins = {_plugin_for_attachment(task, attachment) for attachment in task.attachments}
            if not plugins:
                plugins = {resolve_plugin_for_leave_task(task)}
            unconfigured = [plugin_name for plugin_name in sorted(plugins) if not is_dify_configured(plugin_name)]
            if unconfigured:
                raise ValueError(dify_configuration_message(unconfigured[0]))
        return self.process_task(task, field_parser_backend=field_parser_backend)

    def process_task(self, task: LeaveAuditTask, field_parser_backend: str | None = None) -> LeaveAuditResult:
        self.repository.update_task_status(task.request_id, LeaveAuditStatus.PROCESSING)
        started = time.perf_counter()
        attachment_id = None
        try:
            if not task.attachments:
                raise ValueError("task has no attachments")
            verification_request: dict[str, Any] = {
                "request_id": task.request_id,
                "leave_request_id": _leave_request_id_from_task(task),
                "leave_type": task.leave_type,
                "applicant_name": task.employee_name,
                "leave_start_date": task.leave_start_date,
                "leave_end_date": task.leave_end_date,
            }
            verification_request.update(dict(task.raw_payload.get("verification_context") or {}))
            field_mapping_config = self._field_mapping_config()
            rule_config = self._rule_config(task.leave_type)

            attachment_results: list[dict[str, Any]] = []
            for attachment in task.attachments:
                attachment_id = attachment.attachment_id
                plugin_name = _plugin_for_attachment(task, attachment)
                filename = _attachment_filename(attachment.attachment_id, attachment.filename, attachment.content_type)
                try:
                    payload = self.adapter.download_attachment(attachment.attachment_url)
                    mock_fields = dict(attachment.metadata.get("mock_fields") or task.raw_payload.get("mock_fields") or {})
                    pages = expand_document_pages(payload, filename=filename, content_type=attachment.content_type)
                    page_runs: list[dict[str, Any]] = []
                    prompt_context = _prompt_context(
                        repository=self.repository,
                        plugin_name=plugin_name,
                        task=task,
                        rule_config=rule_config,
                    )
                    for page in pages:
                        analysis_result = self.inference_service.run(
                            plugin_name=plugin_name,
                            image=page.content,
                            filename=page.filename or filename,
                            fields=mock_fields,
                            field_parser_backend=field_parser_backend,
                            prompt_context=prompt_context,
                        )
                        page_runs.append({"page": page, "analysis": analysis_result["analysis"]})
                    analysis_json = _merge_page_analyses(
                        plugin_name=plugin_name,
                        attachment_id=attachment.attachment_id,
                        source_filename=filename,
                        source_content_type=attachment.content_type,
                        page_runs=page_runs,
                    )
                    analysis_json.setdefault("raw_artifacts", {})["prompt_context"] = prompt_context
                    verification_json = verify_attachment(
                        analysis_json,
                        verification_request,
                        field_mapping_config=field_mapping_config,
                        rule_config=rule_config,
                    )
                    status = LeaveAuditStatus(str(verification_json.get("verify_status") or "REVIEW"))
                    attachment_results.append(
                        {
                            "attachment_id": attachment.attachment_id,
                            "filename": filename,
                            "content_type": attachment.content_type,
                            "plugin_name": plugin_name,
                            "status": status,
                            "analysis_json": analysis_json,
                            "verification_json": verification_json,
                            "error_message": None,
                        }
                    )
                except Exception as exc:
                    attachment_results.append(
                        {
                            "attachment_id": attachment.attachment_id,
                            "filename": filename,
                            "content_type": attachment.content_type,
                            "plugin_name": plugin_name,
                            "status": LeaveAuditStatus.ERROR,
                            "analysis_json": {},
                            "verification_json": {},
                            "error_message": f"{exc.__class__.__name__}: {exc}",
                        }
                    )
            selected = min(attachment_results, key=lambda item: _status_rank(item["status"]))
            status = selected["status"]
            summaries = [_attachment_result_summary(item) for item in attachment_results]
            if status == LeaveAuditStatus.ERROR:
                result = LeaveAuditResult(
                    request_id=task.request_id,
                    status=LeaveAuditStatus.ERROR,
                    plugin_name=selected["plugin_name"],
                    analysis_json={},
                    verification_json={"attachment_results": summaries},
                    error_message=selected["error_message"],
                )
            else:
                analysis_json = dict(selected["analysis_json"])
                analysis_json.setdefault("raw_artifacts", {})["attachment_results"] = summaries
                verification_json = dict(selected["verification_json"])
                verification_json["attachment_results"] = summaries
                verification_json["selected_attachment_id"] = selected["attachment_id"]
                result = LeaveAuditResult(
                    request_id=task.request_id,
                    status=status,
                    plugin_name=selected["plugin_name"],
                    analysis_json=analysis_json,
                    verification_json=verification_json,
                )
        except Exception as exc:
            result = LeaveAuditResult(
                request_id=task.request_id,
                status=LeaveAuditStatus.ERROR,
                analysis_json={},
                verification_json={},
                error_message=f"{exc.__class__.__name__}: {exc}",
            )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self.repository.save_result(result)
        self.repository.update_task_status(task.request_id, result.status)
        _log_audit_event(
            request_id=task.request_id,
            leave_request_id=_leave_request_id_from_task(task),
            attachment_id=attachment_id,
            adapter_type=_adapter_type(self.adapter),
            adapter_action="process_task",
            http_status=None,
            elapsed_ms=f"{elapsed_ms:.2f}",
            dry_run=is_leave_audit_dry_run(),
            error_type=None if result.status != LeaveAuditStatus.ERROR else "processing_error",
            error_message=result.error_message,
        )
        return result

    def _field_mapping_config(self) -> dict[str, list[str]]:
        config = {key: list(values) for key, values in DEFAULT_FIELD_MAPPING_CONFIG.items()}
        config.update(self.repository.get_field_mappings())
        return config

    def _rule_config(self, leave_type: str) -> dict[str, Any] | None:
        normalized_leave_type = str(leave_type).upper()
        stored = self.repository.get_rule_config(normalized_leave_type)
        if stored is not None:
            return stored
        return DEFAULT_RULE_CONFIGS.get(normalized_leave_type)

    def push_callback(self, request_id: str) -> LeaveAuditResult:
        result, _ = self.push_callback_with_metadata(request_id)
        return result

    def push_callback_with_metadata(self, request_id: str) -> tuple[LeaveAuditResult, dict[str, Any]]:
        result = self.repository.get_result(request_id)
        if result is None:
            raise KeyError(f"Leave audit result not found: {request_id}")
        started = time.perf_counter()
        dry_run = is_leave_audit_dry_run()
        callback_payload = _callback_payload_from_result(result)
        metadata = {"dry_run": dry_run, "callback_skipped": dry_run, "callback_payload": callback_payload}
        error_type = None
        error_message = None
        try:
            if dry_run:
                result.verification_json = dict(result.verification_json or {})
                result.verification_json["callback_dry_run"] = {
                    "dry_run": True,
                    "callback_skipped": True,
                    "payload": callback_payload,
                }
            else:
                self.adapter.push_audit_result(result)
                result.synced = True
                self.repository.update_task_status(request_id, LeaveAuditStatus.SYNCED)
            self.repository.save_result(result)
            return result, metadata
        except Exception as exc:
            error_type = exc.__class__.__name__
            error_message = str(exc)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            _log_audit_event(
                request_id=request_id,
                leave_request_id=callback_payload.get("leave_request_id"),
                attachment_id=None,
                adapter_type=_adapter_type(self.adapter),
                adapter_action="callback",
                http_status=None,
                elapsed_ms=f"{elapsed_ms:.2f}",
                dry_run=dry_run,
                error_type=error_type,
                error_message=error_message,
            )
