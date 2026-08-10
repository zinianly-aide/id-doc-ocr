from __future__ import annotations

from enum import Enum


class OcrJobStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DEAD = "DEAD"


class DecisionStatus(str, Enum):
    PENDING = "PENDING"
    ANALYZED = "ANALYZED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    PASS = "PASS"
    REJECT = "REJECT"


class CallbackStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DEAD = "DEAD"


class AggregationPolicy(str, Enum):
    ALL_REQUIRED = "ALL_REQUIRED"
    ANY_SUFFICIENT = "ANY_SUFFICIENT"
    REQUIRED_GROUPS = "REQUIRED_GROUPS"

