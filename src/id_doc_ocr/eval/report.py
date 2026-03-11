from __future__ import annotations
from pydantic import BaseModel, Field


class FieldMetric(BaseModel):
    field_name: str
    exact_match: float | None = None
    f1: float | None = None
    support: int = 0


class EvaluationReport(BaseModel):
    plugin_name: str
    overall_exact_match: float | None = None
    document_success_rate: float | None = None
    review_rate: float | None = None
    fields: list[FieldMetric] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
