from pydantic import BaseModel, Field


class DatasetSample(BaseModel):
    sample_id: str
    doc_type: str
    image_path: str
    annotation_path: str | None = None
    split: str | None = None
    tags: list[str] = Field(default_factory=list)


class DatasetManifest(BaseModel):
    name: str
    version: str = "0.1.0"
    samples: list[DatasetSample] = Field(default_factory=list)
