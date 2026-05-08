import type { ApprovalVerificationViewModel } from "../types.ts";

export interface StructuredFieldPresentation {
  contextNotice: string;
  emphasisTone: "pass" | "review";
  badgeText: string | null;
  reviewHint: string | null;
}

const CONTEXT_NOTICE = "以下字段为后端基于当前业务上下文与附件核验结果生成，若附件与业务材料不匹配，请以后端风险提示和人工复核为准。";

const REVIEW_SIGNAL_PATTERN = /(低置信|低可信|置信度|不匹配|无法确认|未能确认|人工复核|ocr|OCR|识别异常|无法识别|不一致|mismatch)/i;

function collectReviewSignals(viewModel: ApprovalVerificationViewModel): string[] {
  return [
    viewModel.verification.summaryMessage,
    ...viewModel.verification.warnings,
    ...viewModel.verification.ruleResults.map((item) => item.message),
    ...viewModel.analysis.validationIssues.map((item) => item.message),
    ...viewModel.analysis.reviewWarnings.map((item) => item.message),
  ].filter(Boolean);
}

export function deriveStructuredFieldPresentation(
  viewModel: ApprovalVerificationViewModel,
): StructuredFieldPresentation {
  const reviewSignals = collectReviewSignals(viewModel);
  const shouldHighlightReview =
    viewModel.verification.verifyStatus === "REVIEW" && (
      viewModel.verification.needsManualReview
      || viewModel.analysis.validationIssues.length > 0
      || viewModel.analysis.reviewWarnings.length > 0
      || reviewSignals.some((signal) => REVIEW_SIGNAL_PATTERN.test(signal))
    );

  if (!shouldHighlightReview) {
    return {
      contextNotice: CONTEXT_NOTICE,
      emphasisTone: "pass",
      badgeText: null,
      reviewHint: null,
    };
  }

  return {
    contextNotice: CONTEXT_NOTICE,
    emphasisTone: "review",
    badgeText: "需复核",
    reviewHint: "当前为人工复核场景，结构化字段仅供辅助核对，不应视为附件内容已被最终确认；若字段与图片观感不一致，请优先参考风险提示并转人工复核。",
  };
}
