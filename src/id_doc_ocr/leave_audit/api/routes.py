from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from id_doc_ocr.application.inference_service import InferenceService
from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.adapters.factory import create_leave_system_adapter
from id_doc_ocr.leave_audit.api.schemas import ReviewRequest
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.leave_audit.service.audit_service import AuditService
from id_doc_ocr.leave_audit.service.review_service import ReviewService
from id_doc_ocr.leave_audit.service.task_service import TaskService

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
def run_task(request: Request, request_id: str) -> dict[str, Any]:
    service = AuditService(_repo(request), _adapter(request), InferenceService(getattr(request.app.state, "settings", None)))
    try:
        result = service.run_task(request_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
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
        result = service.push_callback(request_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return jsonable_encoder({"result": _result_to_dict(result)})


@router.get("/stats")
def stats(request: Request) -> dict[str, Any]:
    return {"stats": _repo(request).stats()}
