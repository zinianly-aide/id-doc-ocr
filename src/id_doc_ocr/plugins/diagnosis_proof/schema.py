from __future__ import annotations

from pydantic import BaseModel, Field


class DiagnosisProofDocument(BaseModel):
    doc_type: str = "diagnosis_proof"
    hospital_name: str | None = None
    certificate_title: str | None = None
    patient_name: str | None = None
    gender: str | None = None
    age: str | None = None
    department: str | None = None
    diagnosis: list[str] = Field(default_factory=list)
    advice: list[str] = Field(default_factory=list)
    issue_date: str | None = None
    rest_start_date: str | None = None
    rest_end_date: str | None = None
    rest_days: int | None = None
    physician_name: str | None = None
    physician_department: str | None = None
    seal_present: bool = False
    seal_text: str | None = None
