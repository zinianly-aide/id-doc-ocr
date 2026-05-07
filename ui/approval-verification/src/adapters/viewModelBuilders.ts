import type {
  ApprovalVerificationViewModel,
  AnalysisViewModel,
  AttachmentViewModel,
  EvidenceEntryViewModel,
  RawAnalyzeResponse,
  RawApprovalVerificationPageModel,
  RawAttachmentItem,
  RawVerifyResponse,
  VerificationViewModel,
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
    docType?: string;
    attachmentLabel?: string;
    verifyStatus?: AttachmentViewModel["verifyStatus"];
  },
): AttachmentViewModel {
  return {
    id: attachment.id,
    filename: attachment.filename,
    contentType: attachment.contentType,
    uploadTime: attachment.uploadTime,
    sizeLabel: attachment.sizeLabel,
    status: attachment.status,
    docType: overrides?.docType ?? attachment.docType ?? null,
    attachmentLabel: overrides?.attachmentLabel ?? attachment.attachmentLabel ?? null,
    verifyStatus: overrides?.verifyStatus ?? attachment.verifyStatus ?? null,
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
  };
}

function buildEvidenceEntries(requestEvidence: Record<string, unknown>): EvidenceEntryViewModel[] {
  return Object.entries(requestEvidence).map(([key, value]) => ({
    key,
    label: humanizeKey(key),
    value: Array.isArray(value) ? value.map((item) => String(item)).join(", ") : renderValue(value),
  }));
}

function buildVerificationViewModel(response: RawVerifyResponse): VerificationViewModel {
  const verification = response.verification;
  return {
    verifyStatus: verification.verify_status,
    riskScore: verification.risk_score,
    riskLevel: verification.risk_level,
    matchedAttachmentType: verification.matched_attachment_type,
    summaryMessage: verification.summary_message,
    needsManualReview: verification.needs_manual_review,
    warnings: verification.warnings,
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

export function buildApprovalPageModel(input: {
  rawPageModel: RawApprovalVerificationPageModel;
  rawAnalyzeResponse?: RawAnalyzeResponse;
  rawVerifyResponse?: RawVerifyResponse;
}): ApprovalVerificationViewModel {
  const analyzeResponse = input.rawVerifyResponse ?? input.rawAnalyzeResponse ?? input.rawPageModel.analyzeResponse;
  const verifyResponse = input.rawVerifyResponse ?? input.rawPageModel.verifyResponse;
  const latestRequestId = input.rawVerifyResponse?.request_id ?? input.rawAnalyzeResponse?.request_id ?? input.rawPageModel.requestHeader.requestId;

  const latestDocType = analyzeResponse.analysis.doc_type;
  const latestAttachmentLabel = analyzeResponse.analysis.classification_evidence.attachment_label;
  const latestVerifyStatus = verifyResponse.verification.verify_status;

  return {
    requestHeader: {
      ...input.rawPageModel.requestHeader,
      requestId: latestRequestId,
    },
    attachments: input.rawPageModel.attachments.map((attachment) =>
      attachment.id === input.rawPageModel.selectedAttachmentId
        ? buildAttachmentViewModel(attachment, {
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
