from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from id_doc_ocr.leave_audit.domain.async_status import (
    AggregationPolicy,
    DecisionStatus,
    OcrJobStatus,
)


@dataclass(frozen=True, slots=True)
class AttachmentDecisionInput:
    attachment_id: str
    ocr_status: OcrJobStatus
    decision_status: DecisionStatus | None = None


@dataclass(frozen=True, slots=True)
class AggregationResult:
    decision_status: DecisionStatus | None
    pending: bool
    reason: str | None = None


def aggregate_attachment_decisions(
    attachments: Iterable[AttachmentDecisionInput],
    policy: AggregationPolicy = AggregationPolicy.ALL_REQUIRED,
) -> AggregationResult:
    """Aggregate attachment decisions without conflating technical errors.

    ``ERROR``/``FAILED`` is deliberately not treated as ``REJECT``. A
    technical failure leaves the task pending until retry or human handling.
    ``REQUIRED_GROUPS`` is reserved for a later policy implementation and is
    rejected explicitly rather than silently falling back to another policy.
    """

    items = tuple(attachments)
    if not items:
        raise ValueError("at least one attachment is required")
    if policy is AggregationPolicy.REQUIRED_GROUPS:
        raise NotImplementedError("REQUIRED_GROUPS requires configured attachment groups")

    unresolved = [
        item
        for item in items
        if item.ocr_status in {OcrJobStatus.CREATED, OcrJobStatus.QUEUED, OcrJobStatus.PROCESSING}
        or item.ocr_status in {OcrJobStatus.FAILED, OcrJobStatus.DEAD}
    ]
    has_failed_ocr = any(item.ocr_status in {OcrJobStatus.FAILED, OcrJobStatus.DEAD} for item in items)
    decisions = [item.decision_status for item in items if item.decision_status is not None]

    if policy is AggregationPolicy.ANY_SUFFICIENT and DecisionStatus.PASS in decisions:
        return AggregationResult(DecisionStatus.PASS, pending=False)

    if DecisionStatus.REJECT in decisions:
        if has_failed_ocr:
            return AggregationResult(None, pending=True, reason="technical_failure_pending")
        return AggregationResult(DecisionStatus.REJECT, pending=False)

    if DecisionStatus.REVIEW_REQUIRED in decisions:
        return AggregationResult(DecisionStatus.REVIEW_REQUIRED, pending=False)

    if unresolved:
        return AggregationResult(None, pending=True, reason="technical_processing_pending" if not has_failed_ocr else "technical_failure_pending")

    if policy is AggregationPolicy.ALL_REQUIRED and all(item.decision_status is DecisionStatus.PASS for item in items):
        return AggregationResult(DecisionStatus.PASS, pending=False)

    return AggregationResult(None, pending=True, reason="decision_missing")
