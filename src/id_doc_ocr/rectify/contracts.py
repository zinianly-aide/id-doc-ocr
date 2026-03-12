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


class RectifyResult(BaseModel):
    image: bytes | str
    perspective: PerspectiveTransform
    orientation: OrientationDecision
    quality: QualityReport
    artifacts: list[RectifyArtifact] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
