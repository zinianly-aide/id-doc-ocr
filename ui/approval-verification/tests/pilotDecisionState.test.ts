import test from "node:test";
import assert from "node:assert/strict";
import { derivePilotDecisionUiState } from "../src/components/pilotDecisionState.ts";
import { deriveStructuredFieldPresentation } from "../src/components/structuredFieldPresentation.ts";

function createReviewLikeViewModel(overrides: Partial<ReturnType<typeof createReviewLikeViewModel>> = {}) {
  return {
    requestHeader: {
      requestId: "REQ-1",
      applicantName: "张三",
      department: "HR",
      leaveType: "SICK",
      leaveDateRange: "2026-04-01 ~ 2026-04-03",
      approvalStatus: "PENDING",
    },
    attachments: [],
    selectedAttachmentId: "att-1",
    analysis: {
      docType: "diagnosis_proof",
      docTypeConfidence: 0.72,
      attachmentLabel: "MEDICAL_CERTIFICATE",
      attachmentConfidence: 0.68,
      matchedKeywords: [],
      extractedFields: [],
      validationAccepted: false,
      validationScore: 0.5,
      validationIssues: [
        {
          code: "ocr_uncertain",
          severity: "warning",
          message: "OCR识别结果置信度较低，无法确认关键字段。",
          fieldName: null,
        },
      ],
      reviewAction: "reject",
      reviewWarnings: [
        {
          code: "manual_review_required",
          severity: "warning",
          message: "材料与当前业务上下文可能不匹配，建议人工复核。",
          stage: null,
          fieldName: null,
        },
      ],
      reviewRecommended: true,
      riskScore: 1,
      riskAction: "REVIEW",
    },
    verification: {
      verifyStatus: "REVIEW",
      riskScore: 1,
      riskLevel: "LOW",
      matchedAttachmentType: "MEDICAL_CERTIFICATE",
      summaryMessage: "REVIEW: attachment requires manual confirmation",
      needsManualReview: true,
      warnings: ["attachment may not match current leave material"],
      ruleResults: [
        {
          ruleCode: "attachment_type_match",
          passed: false,
          severity: "warning",
          scoreDelta: -0.2,
          message: "无法确认附件是否与当前业务材料匹配",
        },
      ],
      requestEvidence: [],
    },
    ...overrides,
  };
}

test("derivePilotDecisionUiState keeps PASS approval summary when verify succeeds", () => {
  const state = derivePilotDecisionUiState({
    verifyStatus: "PASS",
    verifyError: null,
  });

  assert.deepEqual(state, {
    suggestionTone: "pass",
    decisionAdvice: "建议通过",
    decisionSubtitle: "材料满足当前审批要求，可直接完成审批。",
    staleResultWarning: null,
  });
});

test("derivePilotDecisionUiState routes to manual handling when verify fails and stale result is shown", () => {
  const state = derivePilotDecisionUiState({
    verifyStatus: "PASS",
    verifyError: "verify failed",
  });

  assert.deepEqual(state, {
    suggestionTone: "review",
    decisionAdvice: "建议人工处理",
    decisionSubtitle: "本次核验失败，请转人工处理；当前页面仍展示上一次结果，仅供参考。",
    staleResultWarning: "当前展示的是上一次核验结果，请勿直接据此完成审批。",
  });
});

test("deriveStructuredFieldPresentation adds context notice for structured fields", () => {
  const presentation = deriveStructuredFieldPresentation(createReviewLikeViewModel());

  assert.equal(
    presentation.contextNotice,
    "以下字段为后端基于当前业务上下文与附件核验结果生成，若附件与业务材料不匹配，请以后端风险提示和人工复核为准。",
  );
});

test("deriveStructuredFieldPresentation marks structured fields as review-only when review signals indicate low confidence or mismatch", () => {
  const presentation = deriveStructuredFieldPresentation(createReviewLikeViewModel());

  assert.equal(presentation.emphasisTone, "review");
  assert.equal(presentation.badgeText, "需复核");
  assert.match(presentation.reviewHint, /结构化字段仅供辅助核对/);
  assert.match(presentation.reviewHint, /人工复核/);
});
