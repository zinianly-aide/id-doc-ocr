from __future__ import annotations

from pydantic import BaseModel


class OnlyChildCertificateDocument(BaseModel):
    doc_type: str = "only_child_certificate"
    certificate_title: str | None = None
    certificate_number: str | None = None
    child_name: str | None = None
    child_gender: str | None = None
    child_birth_date: str | None = None
    father_name: str | None = None
    mother_name: str | None = None
    issue_date: str | None = None
    issuing_authority: str | None = None
    holder_address: str | None = None
    remarks: str | None = None
