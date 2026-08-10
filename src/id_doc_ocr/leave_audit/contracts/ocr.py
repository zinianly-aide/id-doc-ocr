from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

OCR_COMMAND_SCHEMA_VERSION = "1.0"
OCR_RESULT_SCHEMA_VERSION = "1.0"


class _ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class OcrCommandV1(_ContractModel):
    """Transport-safe OCR command published by Leave Audit Service."""

    schema_version: Literal["1.0"] = OCR_COMMAND_SCHEMA_VERSION
    command_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    attachment_id: str = Field(min_length=1)
    object_key: str = Field(min_length=1)
    content_sha256: str = Field(min_length=1)
    plugin_name: str = Field(min_length=1)
    pipeline_profile: str = Field(min_length=1)
    ocr_profile_snapshot_id: str = Field(min_length=1)
    attempt: int = Field(default=1, ge=1)
    trace_id: str = Field(min_length=1)
    created_at: datetime

    @field_validator("content_sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        normalized = value.lower()
        if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
            raise ValueError("content_sha256 must be a 64-character hexadecimal digest")
        return normalized


class OcrResultEventV1(_ContractModel):
    """Small OCR result event; the full analysis is stored in object storage."""

    schema_version: Literal["1.0"] = OCR_RESULT_SCHEMA_VERSION
    event_id: str = Field(min_length=1)
    causation_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    attachment_id: str = Field(min_length=1)
    status: Literal["SUCCEEDED", "FAILED"]
    result_object_key: str | None = None
    result_sha256: str | None = None
    page_count: int | None = Field(default=None, ge=0)
    engine_version: str = Field(min_length=1)
    pipeline_profile: str = Field(min_length=1)
    ocr_profile_snapshot_id: str = Field(min_length=1)
    started_at: datetime
    completed_at: datetime
    trace_id: str = Field(min_length=1)
    error_code: str | None = None
    error_category: Literal["TRANSIENT", "PERMANENT"] | None = None
    retryable: bool = False
    safe_error_message: str | None = None

    @field_validator("result_sha256")
    @classmethod
    def validate_result_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.lower()
        if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
            raise ValueError("result_sha256 must be a 64-character hexadecimal digest")
        return normalized

    @field_validator("result_object_key")
    @classmethod
    def validate_result_key(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("result_object_key must not be blank when provided")
        return value

    @model_validator(mode="after")
    def validate_error_fields(self) -> "OcrResultEventV1":
        # A failed event must carry a safe, classified error. A successful
        # event must not accidentally expose an error category.
        if self.status == "FAILED" and self.error_category is None:
            raise ValueError("failed OCR events require error_category")
        if self.status == "SUCCEEDED" and self.error_category is not None:
            raise ValueError("successful OCR events must not carry error_category")
        if self.status == "SUCCEEDED" and (self.result_object_key is None or self.result_sha256 is None):
            raise ValueError("successful OCR events require result_object_key and result_sha256")
        if self.status == "FAILED" and self.retryable and self.error_category != "TRANSIENT":
            raise ValueError("retryable OCR events must use TRANSIENT error_category")
        return self
