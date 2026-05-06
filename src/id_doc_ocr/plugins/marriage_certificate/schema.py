from __future__ import annotations

from pydantic import BaseModel


class MarriageCertificateDocument(BaseModel):
    doc_type: str = "marriage_certificate"
    certificate_title: str | None = None
    holder_name: str | None = None
    registration_date: str | None = None
    certificate_number: str | None = None
    registration_officer: str | None = None
    registration_authority: str | None = None
    person_a_name: str | None = None
    person_a_nationality: str | None = None
    person_a_id_number: str | None = None
    person_b_name: str | None = None
    person_b_nationality: str | None = None
    person_b_id_number: str | None = None
