"""Versioned contracts shared by Leave Audit Service and OCR workers.

The contracts intentionally contain transport-safe metadata only. Binary
attachments and large OCR payloads are addressed through object storage.
"""

from id_doc_ocr.leave_audit.contracts.ocr import (
    OCR_COMMAND_SCHEMA_VERSION,
    OCR_RESULT_SCHEMA_VERSION,
    OcrCommandV1,
    OcrResultEventV1,
)

__all__ = [
    "OCR_COMMAND_SCHEMA_VERSION",
    "OCR_RESULT_SCHEMA_VERSION",
    "OcrCommandV1",
    "OcrResultEventV1",
]
