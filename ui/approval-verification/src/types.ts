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

export interface AttachmentItem {
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

export interface ExtractedField {
  name: string;
  value: unknown;
  confidence: number | null;
  source: string | null;
  bbox: Record<string, unknown> | null;
  evidence_text: string | null;
  matched: boolean;
}

export interface ValidationIssue {
  code: string;
  severity: string;
  message: string;
  field_name?: string | null;
}

export interface ReviewWarning {
  code: string;
  severity: string;
  message: string;
  stage?: string;
  field_name?: string | null;
}

export interface AnalysisResponse {
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
    extracted_fields: ExtractedField[];
    validation: {
      accepted: boolean;
      score: number;
      issues: ValidationIssue[];
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
      warnings: ReviewWarning[];
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

export interface RuleResult {
  rule_code: string;
  passed: boolean;
  severity: "info" | "warning" | "error";
  score_delta: number;
  message: string;
  evidence: Record<string, unknown>;
}

export interface VerificationResponse extends AnalysisResponse {
  verification: {
    verify_status: VerifyStatus;
    risk_score: number;
    risk_level: RiskLevel;
    matched_attachment_type: string;
    extracted_fields: Record<string, unknown>;
    rule_results: RuleResult[];
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

export interface ApprovalVerificationMockPage {
  requestHeader: RequestHeader;
  attachments: AttachmentItem[];
  selectedAttachmentId: string;
  analyzeResponse: AnalysisResponse;
  verifyResponse: VerificationResponse;
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
