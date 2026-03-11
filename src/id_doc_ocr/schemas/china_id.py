from pydantic import BaseModel, Field


class ChinaResidentIdCardFront(BaseModel):
    doc_type: str = "china_resident_id_front"
    name: str | None = None
    gender: str | None = None
    ethnicity: str | None = None
    birth_date: str | None = None
    address: str | None = None
    id_number: str | None = None


class ChinaResidentIdCardBack(BaseModel):
    doc_type: str = "china_resident_id_back"
    issuing_authority: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None


class ChinaResidentIdCardDocument(BaseModel):
    front: ChinaResidentIdCardFront | None = None
    back: ChinaResidentIdCardBack | None = None
    warnings: list[str] = Field(default_factory=list)
