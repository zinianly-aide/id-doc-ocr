from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    decision: str = Field(..., description="PASS, REVIEW, REJECT, or IGNORED")
    reviewer: str
    comment: str | None = None


class FieldMappingItem(BaseModel):
    canonical_field: str
    candidates: list[str]


class FieldMappingUpdateRequest(BaseModel):
    mappings: list[FieldMappingItem]


class RuleConfigItem(BaseModel):
    leave_type: str
    prompt_text: str = ""
    rules: list[dict[str, Any]] = Field(default_factory=list)
    enabled: bool = True


class RuleConfigUpdateRequest(BaseModel):
    configs: list[RuleConfigItem]


class PromptConfigItem(BaseModel):
    recognition_type: str = Field(..., description="Plugin/recognition type, for example diagnosis_proof, marriage_certificate, or *")
    prompt_type: str = Field(..., description="Prompt purpose, for example field_extraction, verification, review_summary")
    prompt_text: str = ""
    enabled: bool = True


class PromptConfigUpdateRequest(BaseModel):
    configs: list[PromptConfigItem]


class TaskListResponse(BaseModel):
    tasks: list[dict[str, Any]]


class SyncResponse(BaseModel):
    synced: int
    tasks: list[dict[str, Any]]
