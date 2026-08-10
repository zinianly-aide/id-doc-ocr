from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from id_doc_ocr.leave_audit.domain.models import utc_now_iso


class ConfigKind(str, Enum):
    OCR_PROFILE = "OCR_PROFILE"
    DECISION_POLICY = "DECISION_POLICY"
    FIELD_MAPPING = "FIELD_MAPPING"
    CALLBACK_POLICY = "CALLBACK_POLICY"


class ConfigStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    RETIRED = "RETIRED"
    ROLLED_BACK = "ROLLED_BACK"


def content_hash(content: dict[str, Any]) -> str:
    encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(slots=True)
class ConfigSnapshot:
    version_id: str
    kind: ConfigKind
    content: dict[str, Any]
    created_by: str
    status: ConfigStatus = ConfigStatus.DRAFT
    approved_by: str | None = None
    published_at: str | None = None
    change_reason: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    content_hash: str = ""

    def __post_init__(self) -> None:
        self.content_hash = self.content_hash or content_hash(self.content)

    def publish(self, approved_by: str) -> None:
        if self.status not in {ConfigStatus.APPROVED, ConfigStatus.PUBLISHED}:
            raise ValueError("only approved config snapshots can be published")
        if not approved_by.strip():
            raise ValueError("approved_by is required")
        self.approved_by = approved_by
        self.status = ConfigStatus.PUBLISHED
        self.published_at = utc_now_iso()

