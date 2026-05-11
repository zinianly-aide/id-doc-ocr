export type VerifyStatus = "PASS" | "REVIEW" | "REJECT";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";
export type AsyncStatus = "idle" | "loading" | "success" | "error";
export type MockScenario = "pass" | "review";
export type DataSourceMode = "mock" | "real";

export interface RequestHeader {
  requestId: string;
  applicantName: string;
  department: string;
  leaveType: string;
  leaveDateRange: string;
  approvalStatus: string;
}

export interface RawAttachmentItem {
  id: string;
  filename: string;
  contentType: string;
  uploadTime: string;
  sizeLabel: string;
  status: string;
  docType?: string;
  attachmentLabel?: string;
  verifyStatus?: VerifyStatus;
}

export interface RawExtractedField {
  name: string;
  value: unknown;
  confidence: number | null;
  source: string | null;
  bbox: Record<string, unknown> | null;
  evidence_text: string | null;
  matched: boolean;
}

export interface RawValidationIssue {
  code: string;
  severity: string;
  message: string;
  field_name?: string | null;
}

export interface RawReviewWarning {
  code: string;
  severity: string;
  message: string;
  stage?: string;
  field_name?: string | null;
}

export interface RawAnalyzeResponse {
  request_id: string;
  filename: string;
  content_type: string;
  result: Record<string, unknown>;
  analysis: {
    doc_type: string;
    doc_type_confidence: number | null;
    classification_evidence: {
      plugin: string;
      detector_doc_type: string | null;
      ocr_backend: string;
      vlm_backend: string;
      attachment_label: string;
      attachment_confidence: number | null;
      matched_keywords: string[];
    };
    extracted_fields: RawExtractedField[];
    validation: {
      accepted: boolean;
      score: number;
      issues: RawValidationIssue[];
    };
    review: {
      decision: {
        action: string;
        review_recommended: boolean;
        auto_accepted: boolean;
        quality_passed: boolean;
        validation_accepted: boolean;
        risk_score: number;
      };
      warnings: RawReviewWarning[];
      evidence: Record<string, unknown>;
    };
    risk: {
      score: number;
      review_action: string;
      review_recommended: boolean;
      quality_passed: boolean;
      validation_accepted: boolean;
    };
    raw_artifacts: Record<string, unknown>;
  };
}

export interface RawRuleResult {
  rule_code: string;
  passed: boolean;
  severity: "info" | "warning" | "error";
  score_delta: number;
  message: string;
  evidence: Record<string, unknown>;
}

export interface RawVerifyResponse extends RawAnalyzeResponse {
  verification: {
    verify_status: VerifyStatus;
    risk_score: number;
    risk_level: RiskLevel;
    matched_attachment_type: string;
    extracted_fields: Record<string, unknown>;
    rule_results: RawRuleResult[];
    warnings: string[];
    evidence: {
      request: Record<string, unknown>;
      fields: Record<string, unknown>;
      classification: Record<string, unknown>;
    };
    needs_manual_review: boolean;
    summary_message: string;
  };
}

export interface RawApprovalVerificationPageModel {
  requestHeader: RequestHeader;
  attachments: RawAttachmentItem[];
  selectedAttachmentId: string;
  analyzeResponse: RawAnalyzeResponse;
  verifyResponse: RawVerifyResponse;
}

export interface DemoRequestConfig {
  plugin_name: string;
  ocr_backend?: string;
  vlm_backend?: string;
  detector_backend?: string;
  rectify_backend?: string;
  expected_attachment_type?: string;
  expected_attachment_types?: string;
  leave_type?: string;
  applicant_name?: string;
  related_person_name?: string;
  related_person_relation?: string;
  leave_start_date?: string;
  leave_end_date?: string;
  fieldOverrides: Record<string, string>;
  sampleFileUrl: string;
  sampleFilename: string;
  sampleContentType: string;
}

export interface AttachmentViewModel {
  id: string;
  filename: string;
  contentType: string;
  uploadTime: string;
  sizeLabel: string;
  status: string;
  docType: string | null;
  attachmentLabel: string | null;
  verifyStatus: VerifyStatus | null;
}

export interface ExtractedFieldViewModel {
  name: string;
  value: unknown;
  displayValue: string;
  confidence: number | null;
  source: string | null;
  matched: boolean;
}

export interface ValidationIssueViewModel {
  code: string;
  severity: string;
  message: string;
  fieldName: string | null;
}

export interface ReviewWarningViewModel {
  code: string;
  severity: string;
  message: string;
  stage: string | null;
  fieldName: string | null;
}

export interface AnalysisViewModel {
  docType: string;
  docTypeConfidence: number | null;
  attachmentLabel: string;
  attachmentConfidence: number | null;
  matchedKeywords: string[];
  extractedFields: ExtractedFieldViewModel[];
  validationAccepted: boolean;
  validationScore: number;
  validationIssues: ValidationIssueViewModel[];
  reviewAction: string;
  reviewWarnings: ReviewWarningViewModel[];
  reviewRecommended: boolean;
  riskScore: number;
  riskAction: string;
  riskCategory: RiskCategoryViewModel;
}

export interface RuleResultViewModel {
  ruleCode: string;
  passed: boolean;
  severity: "info" | "warning" | "error";
  scoreDelta: number;
  message: string;
}

export interface EvidenceEntryViewModel {
  key: string;
  label: string;
  value: string;
}

export interface RiskCategoryViewModel {
  label: string;
  level: RiskLevel;
  summary: string;
}

export interface ExplainabilityGroupViewModel {
  key: "ocr_quality" | "document_integrity" | "rule_mismatch";
  label: string;
  items: string[];
}

export interface AutoPassReadinessViewModel {
  status: "ready" | "blocked" | "unknown";
  label: string;
  reasons: string[];
  blockers: string[];
}

export interface VerificationViewModel {
  verifyStatus: VerifyStatus;
  riskScore: number;
  riskLevel: RiskLevel;
  matchedAttachmentType: string;
  summaryMessage: string;
  needsManualReview: boolean;
  warnings: string[];
  reviewReasonHint: string | null;
  reviewReasonTags: string[];
  autoPassReadiness: AutoPassReadinessViewModel;
  riskCategory: RiskCategoryViewModel;
  explainabilityGroups: ExplainabilityGroupViewModel[];
  ruleResults: RuleResultViewModel[];
  requestEvidence: EvidenceEntryViewModel[];
}

export interface ApprovalVerificationViewModel {
  requestHeader: RequestHeader;
  attachments: AttachmentViewModel[];
  selectedAttachmentId: string;
  analysis: AnalysisViewModel;
  verification: VerificationViewModel;
}
