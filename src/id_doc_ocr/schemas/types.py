from typing import Any, Literal
from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float
    y: float


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DocumentDetection(BaseModel):
    doc_type: str | None = None
    bbox: BoundingBox
    corners: list[Point] = Field(default_factory=list)
    confidence: float


class QualityReport(BaseModel):
    blur_score: float | None = None
    glare_score: float | None = None
    occlusion_score: float | None = None
    passed: bool = True
    reasons: list[str] = Field(default_factory=list)


class OCRFieldResult(BaseModel):
    field_name: str
    value: str | None = None
    confidence: float | None = None
    bbox: BoundingBox | None = None
    source: Literal["template_ocr", "mrz", "barcode", "vlm_fallback", "manual"]


class StructuredDocument(BaseModel):
    doc_type: str
    country_code: str | None = None
    fields: dict[str, Any] = Field(default_factory=dict)
    field_results: list[OCRFieldResult] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "error"]
    field_name: str | None = None


class ValidationReport(BaseModel):
    accepted: bool
    score: float | None = None
    issues: list[ValidationIssue] = Field(default_factory=list)
