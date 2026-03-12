from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from id_doc_ocr.schemas.types import BoundingBox, DocumentDetection, Point


class DocumentQuad(BaseModel):
    points: list[Point] = Field(default_factory=list)


class DocumentClassification(BaseModel):
    label: str
    confidence: float


class DetectorResult(BaseModel):
    primary: DocumentDetection
    quad: DocumentQuad | None = None
    classifications: list[DocumentClassification] = Field(default_factory=list)
    model_version: str = "mock"
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def bbox(self) -> BoundingBox:
        return self.primary.bbox

    @property
    def doc_type(self) -> str | None:
        return self.primary.doc_type
