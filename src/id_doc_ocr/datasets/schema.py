from __future__ import annotations
from pydantic import BaseModel, Field


class PolygonPoint(BaseModel):
    x: float
    y: float


class RegionAnnotation(BaseModel):
    region_id: str
    label: str
    bbox: list[float] | None = None
    polygon: list[PolygonPoint] = Field(default_factory=list)
    text: str | None = None
    attributes: dict = Field(default_factory=dict)


class FieldAnnotation(BaseModel):
    field_name: str
    value: str | None = None
    region_id: str | None = None
    confidence: float | None = None
    attributes: dict = Field(default_factory=dict)


class RelationAnnotation(BaseModel):
    from_id: str
    to_id: str
    relation_type: str


class QualityTag(BaseModel):
    tag: str
    score: float | None = None
    note: str | None = None


class InternalAnnotation(BaseModel):
    sample_id: str
    doc_type: str
    regions: list[RegionAnnotation] = Field(default_factory=list)
    fields: list[FieldAnnotation] = Field(default_factory=list)
    relations: list[RelationAnnotation] = Field(default_factory=list)
    quality_tags: list[QualityTag] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
