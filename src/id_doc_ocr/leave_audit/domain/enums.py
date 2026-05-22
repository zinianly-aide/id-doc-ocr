from __future__ import annotations

from enum import Enum


class LeaveAuditStatus(str, Enum):
    PENDING = "PENDING"
    PULLED = "PULLED"
    PROCESSING = "PROCESSING"
    PASS = "PASS"
    REVIEW = "REVIEW"
    REJECT = "REJECT"
    ERROR = "ERROR"
    IGNORED = "IGNORED"
    SYNCED = "SYNCED"
