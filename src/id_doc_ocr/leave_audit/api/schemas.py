from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    decision: str = Field(..., description="PASS, REVIEW, REJECT, or IGNORED")
    reviewer: str
    comment: str | None = None


class TaskListResponse(BaseModel):
    tasks: list[dict[str, Any]]


class SyncResponse(BaseModel):
    synced: int
    tasks: list[dict[str, Any]]
