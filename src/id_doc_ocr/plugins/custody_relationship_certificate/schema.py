from __future__ import annotations

from pydantic import BaseModel, Field


class CustodyRelationshipCertificateDocument(BaseModel):
    doc_type: str = "custody_relationship_certificate"
    certificate_title: str | None = None
    child_name: str | None = None
    guardian_name: str | None = None
    relation: str | None = None
    relation_statement: str | None = None
    child_birth_date: str | None = None
    child_id_number: str | None = None
    guardian_id_number: str | None = None
    subject_address: str | None = None
    purpose: str | None = None
    issuing_authority: str | None = None
    issue_date: str | None = None
    authority_features: list[str] = Field(default_factory=list)
