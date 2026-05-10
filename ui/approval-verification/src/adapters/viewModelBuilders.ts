import type {
  ApprovalVerificationViewModel,
  AnalysisViewModel,
  AttachmentViewModel,
  EvidenceEntryViewModel,
  RawAnalyzeResponse,
  RawApprovalVerificationPageModel,
  RawAttachmentItem,
  RawVerifyResponse,
  RiskCategoryViewModel,
  VerificationViewModel,
  VerifyStatus,
} from "@/types";

function renderValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.length ? value.map((item) => String(item)).join(", ") : "[]";
  }
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function humanizeKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\w/g, (char) => char.toUpperCase());
}

function buildAttachmentViewModel(
  attachment: RawAttachmentItem,
  overrides?: {
    filename?: string;
    docType?: string;
    attachmentLabel?: string;
    verifyStatus?: VerifyStatus;
  },
): AttachmentViewModel {
  return {
    id: attachment.id,
    filename: overrides?.filename ?? attachment.filename,
    contentType: attachment.contentType,
    uploadTime: attachment.uploadTime,
    sizeLabel: attachment.sizeLabel,
    status: attachment.status,
    docType: overrides?.docType ?? attachment.docType ?? null,
    attachmentLabel: overrides?.attachmentLabel ?? attachment.attachmentLabel ?? null,
    verifyStatus: overrides?.verifyStatus ?? attachment.verifyStatus ?? null,
  };
}

function deriveAnalysisRiskCategory(response: RawAnalyzeResponse): RiskCategoryViewModel {
  const analysis = response.analysis;
  const level = analysis.risk.review_recommended || !analysis.risk.quality_passed
    ? "HIGH"
    : analysis.risk.score >= 0.35 || !analysis.risk.validation_accepted
      ? "MEDIUM"
      : "LOW";

  let summary = "识别链路未发现明显材料风险，可继续参考业务核验结论。";
  if (!analysis.risk.quality_passed) {
    summary = "材料质量门控尚未通过，识别链路仍建议人工复核。";
  } else if (!analysis.risk.validation_accepted) {
    summary = "结构化字段校验仍有缺口，识别链路建议补充核对原始材料。";
  } else if (analysis.review.decision.review_recommended) {
    summary = "识别链路仍保留人工复核建议，暂未达到自动通过标准。";
  }

  return {
    label: "识别/材料风险",
    level,
    summary,
  };
}

function buildAnalysisViewModel(response: RawAnalyzeResponse): AnalysisViewModel {
  const analysis = response.analysis;
  return {
    docType: analysis.doc_type,
    docTypeConfidence: analysis.doc_type_confidence,
    attachmentLabel: analysis.classification_evidence.attachment_label,
    attachmentConfidence: analysis.classification_evidence.attachment_confidence,
    matchedKeywords: analysis.classification_evidence.matched_keywords,
    extractedFields: analysis.extracted_fields.map((field) => ({
      name: field.name,
      value: field.value,
      displayValue: renderValue(field.value),
      confidence: field.confidence,
      source: field.source,
      matched: field.matched,
    })),
    validationAccepted: analysis.validation.accepted,
    validationScore: analysis.validation.score,
    validationIssues: analysis.validation.issues.map((issue) => ({
      code: issue.code,
      severity: issue.severity,
      message: issue.message,
      fieldName: issue.field_name ?? null,
    })),
    reviewAction: analysis.review.decision.action,
    reviewWarnings: analysis.review.warnings.map((warning) => ({
      code: warning.code,
      severity: warning.severity,
      message: warning.message,
      stage: warning.stage ?? null,
      fieldName: warning.field_name ?? null,
    })),
    reviewRecommended: analysis.review.decision.review_recommended,
    riskScore: analysis.risk.score,
    riskAction: analysis.risk.review_action,
    riskCategory: deriveAnalysisRiskCategory(response),
  };
}

function buildEvidenceEntries(requestEvidence: Record<string, unknown>): EvidenceEntryViewModel[] {
  return Object.entries(requestEvidence).map(([key, value]) => ({
    key,
    label: humanizeKey(key),
    value: Array.isArray(value) ? value.map((item) => String(item)).join(", ") : renderValue(value),
  }));
}

function hasMeaningfulValue(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "string") return value.trim().length > 0;
  return value !== null && value !== undefined;
}

function buildReviewReasonHint(response: RawVerifyResponse): string | null {
  const verification = response.verification;
  if (verification.verify_status !== "REVIEW" || verification.needs_manual_review !== true) {
    return null;
  }
  if (verification.warnings.length > 0) {
    return null;
  }

  const hasExplicitRuleFailure = verification.rule_results.some((rule) => rule.passed === false);
  if (hasExplicitRuleFailure) {
    return null;
  }

  const extractedFieldMap = new Map(response.analysis.extracted_fields.map((field) => [field.name, field.value]));
  const hasCompleteCoreFields = ["patient_name", "rest_start_date", "rest_end_date", "issue_date"].every((fieldName) =>
    hasMeaningfulValue(extractedFieldMap.get(fieldName)),
  );
  if (!hasCompleteCoreFields) {
    return null;
  }

  return "业务字段已基本匹配，但材料质量门控/识别置信度仍未达到自动通过标准，建议人工复核。";
}

function deriveVerificationRiskCategory(response: RawVerifyResponse, reviewReasonHint: string | null): RiskCategoryViewModel {
  const verification = response.verification;
  let summary = "业务规则未发现明显冲突，可按当前核验结论继续审批。";

  if (verification.verify_status === "REJECT" || verification.risk_level === "HIGH") {
    summary = "业务规则已发现高风险冲突，建议驳回或退回补正。";
  } else if (verification.warnings.length > 0) {
    summary = "业务规则命中了需复核的预警项，建议结合原始材料继续核对。";
  } else if (reviewReasonHint) {
    summary = "业务字段已基本匹配，业务规则侧未发现明显冲突。";
  } else if (verification.verify_status === "REVIEW") {
    summary = "业务核验结论仍为人工复核，建议继续查看规则明细。";
  }

  return {
    label: "业务核验风险",
    level: verification.risk_level,
    summary,
  };
}

function buildVerificationViewModel(response: RawVerifyResponse): VerificationViewModel {
  const verification = response.verification;
  const reviewReasonHint = buildReviewReasonHint(response);
  return {
    verifyStatus: verification.verify_status,
    riskScore: verification.risk_score,
    riskLevel: verification.risk_level,
    matchedAttachmentType: verification.matched_attachment_type,
    summaryMessage: verification.summary_message,
    needsManualReview: verification.needs_manual_review,
    warnings: verification.warnings,
    reviewReasonHint,
    riskCategory: deriveVerificationRiskCategory(response, reviewReasonHint),
    ruleResults: verification.rule_results.map((rule) => ({
      ruleCode: rule.rule_code,
      passed: rule.passed,
      severity: rule.severity,
      scoreDelta: rule.score_delta,
      message: rule.message,
    })),
    requestEvidence: buildEvidenceEntries(verification.evidence.request),
  };
}

function assertAnalyzePayload(response: unknown, context: "analyze" | "verify"): asserts response is RawAnalyzeResponse {
  if (!response || typeof response !== "object" || !("analysis" in response) || !(response as { analysis?: unknown }).analysis) {
    throw new Error(`${context} response is missing analysis payload`);
  }
}

function assertVerifyPayload(response: unknown): asserts response is RawVerifyResponse {
  if (!response || typeof response !== "object" || !("verification" in response) || !(response as { verification?: unknown }).verification) {
    throw new Error("verify response is missing verification payload");
  }
}

function pickNonEmptyString(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim().length > 0 ? value : fallback;
}

function buildLeaveDateRange(start: unknown, end: unknown, fallback: string): string {
  if (typeof start === "string" && start.trim() && typeof end === "string" && end.trim()) {
    return `${start} ~ ${end}`;
  }
  return fallback;
}

export function buildApprovalPageModel(input: {
  rawPageModel: RawApprovalVerificationPageModel;
  rawAnalyzeResponse?: RawAnalyzeResponse;
  rawVerifyResponse?: RawVerifyResponse;
}): ApprovalVerificationViewModel {
  const analyzeResponse = input.rawVerifyResponse ?? input.rawAnalyzeResponse ?? input.rawPageModel.analyzeResponse;
  const verifyResponse = input.rawVerifyResponse ?? input.rawPageModel.verifyResponse;
  const latestRequestId = input.rawVerifyResponse?.request_id ?? input.rawAnalyzeResponse?.request_id ?? input.rawPageModel.requestHeader.requestId;

  assertAnalyzePayload(analyzeResponse, input.rawVerifyResponse ? "verify" : "analyze");
  assertVerifyPayload(verifyResponse);

  const latestDocType = analyzeResponse.analysis.doc_type;
  const latestAttachmentLabel = analyzeResponse.analysis.classification_evidence.attachment_label;
  const latestVerifyStatus = verifyResponse.verification.verify_status;
  const latestFilename = input.rawVerifyResponse?.filename ?? input.rawAnalyzeResponse?.filename ?? null;
  const latestRequestContext = input.rawVerifyResponse?.verification.evidence?.request ?? null;

  return {
    requestHeader: {
      ...input.rawPageModel.requestHeader,
      requestId: latestRequestId,
      applicantName: pickNonEmptyString(latestRequestContext?.applicant_name, input.rawPageModel.requestHeader.applicantName),
      leaveType: pickNonEmptyString(latestRequestContext?.leave_type, input.rawPageModel.requestHeader.leaveType),
      leaveDateRange: buildLeaveDateRange(
        latestRequestContext?.leave_start_date,
        latestRequestContext?.leave_end_date,
        input.rawPageModel.requestHeader.leaveDateRange,
      ),
    },
    attachments: input.rawPageModel.attachments.map((attachment) =>
      attachment.id === input.rawPageModel.selectedAttachmentId
        ? buildAttachmentViewModel(attachment, {
            filename: latestFilename ?? attachment.filename,
            docType: latestDocType,
            attachmentLabel: latestAttachmentLabel,
            verifyStatus: latestVerifyStatus,
          })
        : buildAttachmentViewModel(attachment),
    ),
    selectedAttachmentId: input.rawPageModel.selectedAttachmentId,
    analysis: buildAnalysisViewModel(analyzeResponse),
    verification: buildVerificationViewModel(verifyResponse),
  };
}
