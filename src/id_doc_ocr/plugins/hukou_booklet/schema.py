from pydantic import BaseModel


class HukouBookletDocument(BaseModel):
    doc_type: str = "hukou_booklet"
    household_id: str | None = None
    householder_name: str | None = None
    address: str | None = None
    member_name: str | None = None
    relation_to_head: str | None = None
    gender: str | None = None
    birth_date: str | None = None
    id_number: str | None = None
