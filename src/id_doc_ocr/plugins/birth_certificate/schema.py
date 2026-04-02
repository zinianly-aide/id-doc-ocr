from __future__ import annotations

from pydantic import BaseModel


class BirthCertificateDocument(BaseModel):
    doc_type: str = "birth_certificate"
    child_name: str | None = None
    sex: str | None = None
    date_of_birth: str | None = None
    time_of_birth: str | None = None
    gestational_weeks: int | None = None
    birth_weight_grams: int | None = None
    birth_place: str | None = None
    issuing_unit: str | None = None
    certificate_number: str | None = None
    mother_name: str | None = None
    mother_age: int | None = None
    father_name: str | None = None
    issue_date: str | None = None
