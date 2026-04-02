from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from id_doc_ocr.schemas.types import Point, QualityReport


class PerspectiveTransform(BaseModel):
    source_corners: list[Point] = Field(default_factory=list)
    target_corners: list[Point] = Field(default_factory=list)
    applied: bool = False
    confidence: float | None = None
    method: str = "mock"


class OrientationDecision(BaseModel):
    angle: Literal[0, 90, 180, 270] = 0
    clockwise: bool = True
    applied: bool = False
    confidence: float | None = None
    method: str = "mock"


class RectifyArtifact(BaseModel):
    stage: str
    payload: dict[str, Any] = Field(default_factory=dict)


class QualityFlag(BaseModel):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    source: Literal["detector", "perspective", "orientation", "quality"]
    metric: str | None = None
    value: float | bool | str | None = None
    threshold: float | bool | str | None = None


class QualitySummary(BaseModel):
    passed: bool = True
    review_recommended: bool = False
    routing_hint: Literal["normal", "review", "reject"] = "normal"
    risk_score: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    flags: list[QualityFlag] = Field(default_factory=list)
    metrics: dict[str, float | bool | str | None] = Field(default_factory=dict)


class RectifyResult(BaseModel):
    image: bytes | str
    perspective: PerspectiveTransform
    orientation: OrientationDecision
    quality: QualityReport
    quality_summary: QualitySummary = Field(default_factory=QualitySummary)
    artifacts: list[RectifyArtifact] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
