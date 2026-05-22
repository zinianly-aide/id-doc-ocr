from __future__ import annotations

from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveReviewDecision
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository


class ReviewService:
    def __init__(self, repository: SQLiteRepository) -> None:
        self.repository = repository

    def submit(self, *, request_id: str, decision: str, reviewer: str, comment: str | None = None) -> LeaveReviewDecision:
        task = self.repository.get_task(request_id)
        if task is None:
            raise KeyError(f"Leave audit task not found: {request_id}")
        status = LeaveAuditStatus(str(decision).upper())
        if status not in {LeaveAuditStatus.PASS, LeaveAuditStatus.REVIEW, LeaveAuditStatus.REJECT, LeaveAuditStatus.IGNORED}:
            raise ValueError("review decision must be PASS, REVIEW, REJECT, or IGNORED")
        review = LeaveReviewDecision(request_id=request_id, decision=status, reviewer=reviewer, comment=comment)
        self.repository.save_review(review)
        return review
