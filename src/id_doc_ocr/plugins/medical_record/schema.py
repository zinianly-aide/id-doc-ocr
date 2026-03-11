from __future__ import annotations
from pydantic import BaseModel, Field


class MedicalRecordDocument(BaseModel):
    doc_type: str = "medical_record"
    hospital_name: str | None = None
    patient_name: str | None = None
    gender: str | None = None
    age: str | None = None
    visit_date: str | None = None
    department: str | None = None
    diagnosis: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    notes: str | None = None
