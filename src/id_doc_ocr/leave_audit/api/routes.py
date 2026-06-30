from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from id_doc_ocr.application.inference_service import InferenceService
from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.adapters.factory import create_leave_system_adapter
from id_doc_ocr.leave_audit.api.schemas import (
    FieldMappingUpdateRequest,
    PromptConfigUpdateRequest,
    ReviewRequest,
    RuleConfigUpdateRequest,
)
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.leave_audit.service.audit_service import AuditService
from id_doc_ocr.leave_audit.service.review_service import ReviewService
from id_doc_ocr.leave_audit.service.task_service import TaskService
from id_doc_ocr.verification.rules import DEFAULT_FIELD_MAPPING_CONFIG, DEFAULT_RULE_CONFIGS

router = APIRouter(prefix="/leave-audit", tags=["leave-audit"])


def _repo(request: Request) -> SQLiteRepository:
    repo = getattr(request.app.state, "leave_audit_repository", None)
    if repo is None:
        repo = SQLiteRepository()
        request.app.state.leave_audit_repository = repo
    return repo


def _adapter(request: Request) -> LeaveSystemAdapter:
    adapter = getattr(request.app.state, "leave_system_adapter", None)
    if adapter is None:
        adapter = create_leave_system_adapter()
        request.app.state.leave_system_adapter = adapter
    return adapter


def _task_to_dict(task) -> dict[str, Any]:
    payload = asdict(task)
    payload["status"] = task.status.value
    return payload


def _result_to_dict(result) -> dict[str, Any] | None:
    if result is None:
        return None
    payload = asdict(result)
    payload["status"] = result.status.value
    return payload


def _review_to_dict(review) -> dict[str, Any]:
    payload = asdict(review)
    payload["decision"] = review.decision.value
    return payload


def _merged_field_mappings(repository: SQLiteRepository) -> dict[str, list[str]]:
    mappings = {key: list(values) for key, values in DEFAULT_FIELD_MAPPING_CONFIG.items()}
    mappings.update(repository.get_field_mappings())
    return mappings


def _merged_rule_configs(repository: SQLiteRepository) -> list[dict[str, Any]]:
    configs = {key: dict(value) for key, value in DEFAULT_RULE_CONFIGS.items()}
    for item in repository.get_rule_configs():
        configs[str(item["leave_type"]).upper()] = item
    return list(configs.values())


CONFIG_GUIDANCE = {
    "field_mapping": [
        "canonical_field 是系统内部字段，例如 applicant_name、related_person_name、leave_start_date、leave_end_date。",
        "candidates 是 OCR/解析结果里可能出现的字段名，系统会按顺序取第一个非空值。",
        "如果材料返回 name 字段，就把 name 加到 applicant_name 的 candidates 中。",
    ],
    "rule_config": [
        "leave_type 使用假别编码，例如 MARRIAGE、SICK。",
        "prompt_text 兼容旧配置：未配置 prompt_config.field_extraction 时，会作为 Dify 字段抽取提示词兜底。",
        "rules 目前支持 date_window 和 required_name。date_window 可配置 date_field、max_years、on_fail；required_name 可配置 candidates、on_fail。",
        "on_fail=REJECT 会直接驳回；否则进入 REVIEW。",
    ],
    "prompt_config": [
        "recognition_type 使用识别插件名，例如 diagnosis_proof、marriage_certificate；也可以用 * 配全局默认。",
        "prompt_type=field_extraction 会传给 Dify 字段解析；workflow 可读取 inputs.custom_prompt，chat/completion 会拼进 query。",
        "prompt_type=verification 用于记录审核口径，并会进入 prompt_texts；当前规则审核仍以 rules JSON 为准。",
        "prompt_type=review_summary、qa_assistant 可先用于沉淀文案，后续接入 LLM 复核或问答时复用。",
    ],
}


@router.get("/tasks")
def list_tasks(request: Request, status: str | None = None) -> dict[str, Any]:
    repository = _repo(request)
    tasks = repository.list_tasks(status=status)
    return jsonable_encoder({"tasks": [_task_to_dict(task) for task in tasks]})


@router.get("/tasks/{request_id}")
def get_task(request: Request, request_id: str) -> dict[str, Any]:
    repository = _repo(request)
    task = repository.get_task(request_id)
    if task is None:
        raise HTTPException(status_code=404, detail="leave audit task not found")
    return jsonable_encoder(
        {
            "task": _task_to_dict(task),
            "result": _result_to_dict(repository.get_result(request_id)),
            "reviews": [_review_to_dict(review) for review in repository.list_reviews(request_id)],
        }
    )


@router.post("/sync")
def sync_tasks(request: Request) -> dict[str, Any]:
    service = TaskService(_repo(request), _adapter(request))
    tasks = service.sync_pending()
    return jsonable_encoder({"synced": len(tasks), "tasks": [_task_to_dict(task) for task in tasks]})


@router.post("/tasks/{request_id}/run")
def run_task(request: Request, request_id: str, field_parser_backend: str | None = None) -> dict[str, Any]:
    service = AuditService(_repo(request), _adapter(request), InferenceService(getattr(request.app.state, "settings", None)))
    try:
        result = service.run_task(request_id, field_parser_backend=field_parser_backend)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return jsonable_encoder({"result": _result_to_dict(result)})


@router.post("/tasks/{request_id}/review")
def review_task(request: Request, request_id: str, body: ReviewRequest) -> dict[str, Any]:
    service = ReviewService(_repo(request))
    try:
        review = service.submit(request_id=request_id, decision=body.decision, reviewer=body.reviewer, comment=body.comment)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return jsonable_encoder({"review": _review_to_dict(review)})


@router.post("/tasks/{request_id}/callback")
def callback_task(request: Request, request_id: str) -> dict[str, Any]:
    service = AuditService(_repo(request), _adapter(request), InferenceService(getattr(request.app.state, "settings", None)))
    try:
        result, metadata = service.push_callback_with_metadata(request_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return jsonable_encoder({"result": _result_to_dict(result), **metadata})


@router.get("/stats")
def stats(request: Request) -> dict[str, Any]:
    return {"stats": _repo(request).stats()}


@router.get("/config")
def get_config(request: Request) -> dict[str, Any]:
    repository = _repo(request)
    return jsonable_encoder(
        {
            "field_mappings": [
                {"canonical_field": key, "candidates": value}
                for key, value in _merged_field_mappings(repository).items()
            ],
            "rule_configs": _merged_rule_configs(repository),
            "prompt_configs": repository.get_prompt_configs(),
            "guidance": CONFIG_GUIDANCE,
        }
    )


@router.put("/config/field-mappings")
def update_field_mappings(request: Request, body: FieldMappingUpdateRequest) -> dict[str, Any]:
    repository = _repo(request)
    for item in body.mappings:
        repository.save_field_mapping(item.canonical_field, item.candidates)
    return jsonable_encoder({"field_mappings": [{"canonical_field": key, "candidates": value} for key, value in _merged_field_mappings(repository).items()]})


@router.put("/config/rules")
def update_rule_configs(request: Request, body: RuleConfigUpdateRequest) -> dict[str, Any]:
    repository = _repo(request)
    for item in body.configs:
        repository.save_rule_config(item.leave_type, item.prompt_text, item.rules, item.enabled)
    return jsonable_encoder({"rule_configs": _merged_rule_configs(repository)})


@router.put("/config/prompts")
def update_prompt_configs(request: Request, body: PromptConfigUpdateRequest) -> dict[str, Any]:
    repository = _repo(request)
    for item in body.configs:
        repository.save_prompt_config(item.recognition_type, item.prompt_type, item.prompt_text, item.enabled)
    return jsonable_encoder({"prompt_configs": repository.get_prompt_configs()})
