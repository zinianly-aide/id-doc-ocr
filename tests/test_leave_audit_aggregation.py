import pytest

from id_doc_ocr.leave_audit.domain.aggregation import AttachmentDecisionInput, aggregate_attachment_decisions
from id_doc_ocr.leave_audit.domain.async_status import AggregationPolicy, DecisionStatus, OcrJobStatus


def resolved(status: DecisionStatus) -> AttachmentDecisionInput:
    return AttachmentDecisionInput("att", OcrJobStatus.SUCCEEDED, status)


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ([DecisionStatus.PASS, DecisionStatus.PASS], DecisionStatus.PASS),
        ([DecisionStatus.PASS, DecisionStatus.REVIEW_REQUIRED], DecisionStatus.REVIEW_REQUIRED),
        ([DecisionStatus.PASS, DecisionStatus.REJECT], DecisionStatus.REJECT),
        ([DecisionStatus.REVIEW_REQUIRED, DecisionStatus.REJECT], DecisionStatus.REJECT),
        ([DecisionStatus.REJECT, DecisionStatus.REJECT], DecisionStatus.REJECT),
    ],
)
def test_all_required_aggregation_truth_table(statuses, expected):
    result = aggregate_attachment_decisions([resolved(status) for status in statuses])
    assert result.decision_status is expected
    assert result.pending is False


@pytest.mark.parametrize(
    "items",
    [
        [AttachmentDecisionInput("pass", OcrJobStatus.SUCCEEDED, DecisionStatus.PASS), AttachmentDecisionInput("error", OcrJobStatus.FAILED)],
        [AttachmentDecisionInput("reject", OcrJobStatus.SUCCEEDED, DecisionStatus.REJECT), AttachmentDecisionInput("error", OcrJobStatus.FAILED)],
        [AttachmentDecisionInput("error-1", OcrJobStatus.FAILED), AttachmentDecisionInput("error-2", OcrJobStatus.DEAD)],
    ],
)
def test_technical_error_never_becomes_business_reject(items):
    result = aggregate_attachment_decisions(items)
    assert result.pending is True
    assert result.decision_status is None


def test_any_sufficient_requires_explicit_policy():
    items = [resolved(DecisionStatus.PASS), resolved(DecisionStatus.REVIEW_REQUIRED)]
    result = aggregate_attachment_decisions(items, policy=AggregationPolicy.ANY_SUFFICIENT)
    assert result.decision_status is DecisionStatus.PASS


def test_required_groups_is_explicitly_unimplemented():
    with pytest.raises(NotImplementedError):
        aggregate_attachment_decisions([resolved(DecisionStatus.PASS)], policy=AggregationPolicy.REQUIRED_GROUPS)
