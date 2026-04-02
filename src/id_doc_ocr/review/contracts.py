from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ReviewWarning(BaseModel):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    source: str
    stage: str
    field_name: str | None = None
    metric: str | None = None
    value: float | bool | str | None = None
    threshold: float | bool | str | None = None


class ReviewDecision(BaseModel):
    action: Literal["accept", "accept_with_warning", "review", "reject"]
    reason_codes: list[str] = Field(default_factory=list)
    review_recommended: bool = False
    auto_accepted: bool = False
    quality_passed: bool = True
    validation_accepted: bool = True
    risk_score: float = 0.0


class ReviewEvidenceItem(BaseModel):
    field_name: str
    value: Any = None
    source: str
    confidence: float | None = None
    bbox: list[float] | None = None
    region_id: str | None = None
    text: str | None = None
    matched: bool = False


class ReviewEvidence(BaseModel):
    ocr_lines: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[ReviewEvidenceItem] = Field(default_factory=list)
    validator_issues: list[dict[str, Any]] = Field(default_factory=list)
    quality_flags: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class ReviewReadyPayload(BaseModel):
    decision: ReviewDecision
    warnings: list[ReviewWarning] = Field(default_factory=list)
    evidence: ReviewEvidence
