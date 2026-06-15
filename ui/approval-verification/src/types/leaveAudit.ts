export type LeaveAuditStatus =
  | "PENDING"
  | "PULLED"
  | "PROCESSING"
  | "PASS"
  | "REVIEW"
  | "REJECT"
  | "ERROR"
  | "IGNORED"
  | "SYNCED";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | string;
export type AutoPassReadinessStatus = "ready" | "blocked" | "unknown" | string;

export interface LeaveAttachment {
  attachment_id: string;
  attachment_url: string;
  filename?: string | null;
  content_type?: string | null;
  plugin_name?: string | null;
  metadata: Record<string, unknown>;
}

export interface LeaveAuditTask {
  request_id: string;
  leave_type: string;
  employee_name: string;
  leave_start_date?: string | null;
  leave_end_date?: string | null;
  status: LeaveAuditStatus;
  attachments: LeaveAttachment[];
  employee_id?: string | null;
  raw_payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AutoPassReadiness {
  status: AutoPassReadinessStatus;
  label: string;
  reasons: string[];
  blockers: string[];
}

export interface RuleResult {
  rule_code: string;
  passed: boolean;
  severity: string;
  score_delta: number;
  message?: string;
  message_zh?: string;
  display_message?: string;
  evidence: Record<string, unknown>;
}

export interface VerificationJson {
  verify_status?: LeaveAuditStatus | string;
  risk_score?: number;
  risk_level?: RiskLevel;
  autoPassReadiness?: AutoPassReadiness;
  matched_attachment_type?: string;
  extracted_fields?: Record<string, unknown>;
  rule_results?: RuleResult[];
  warnings?: string[];
  evidence?: Record<string, unknown>;
  needs_manual_review?: boolean;
  summary_message?: string;
  [key: string]: unknown;
}

export interface AnalysisJson {
  doc_type?: string;
  doc_type_confidence?: number | null;
  classification_evidence?: Record<string, unknown>;
  extracted_fields?: Array<Record<string, unknown>>;
  validation?: Record<string, unknown>;
  review?: Record<string, unknown>;
  risk?: Record<string, unknown>;
  raw_artifacts?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface LeaveAuditResult {
  request_id: string;
  status: LeaveAuditStatus;
  plugin_name?: string | null;
  analysis_json: AnalysisJson;
  verification_json: VerificationJson;
  error_message?: string | null;
  synced: boolean;
  created_at: string;
  updated_at: string;
}

export interface LeaveReviewDecision {
  request_id: string;
  decision: LeaveAuditStatus;
  reviewer: string;
  comment?: string | null;
  created_at: string;
}

export interface LeaveAuditDetailResponse {
  task: LeaveAuditTask;
  result: LeaveAuditResult | null;
  reviews: LeaveReviewDecision[];
}

export interface LeaveAuditTaskListResponse {
  tasks: LeaveAuditTask[];
}

export interface LeaveAuditSyncResponse {
  synced: number;
  tasks: LeaveAuditTask[];
}

export interface LeaveAuditResultResponse {
  result: LeaveAuditResult;
}

export interface LeaveAuditReviewResponse {
  review: LeaveReviewDecision;
}

export interface LeaveAuditStatsResponse {
  stats: Partial<Record<LeaveAuditStatus, number>>;
}

export interface FieldMappingItem {
  canonical_field: string;
  candidates: string[];
}

export interface RuleConfigItem {
  leave_type: string;
  prompt_text: string;
  rules: Array<Record<string, unknown>>;
  enabled: boolean;
  updated_at?: string;
}

export interface LeaveAuditConfigGuidance {
  field_mapping: string[];
  rule_config: string[];
}

export interface LeaveAuditConfigResponse {
  field_mappings: FieldMappingItem[];
  rule_configs: RuleConfigItem[];
  guidance: LeaveAuditConfigGuidance;
}

export interface OcrLine {
  text?: string;
  score?: number;
  box?: unknown;
  [key: string]: unknown;
}

export interface OcrResponse {
  filename?: string | null;
  content_type?: string | null;
  ocr_backend: string;
  text: string | string[];
  lines: OcrLine[];
  confidence?: number | null;
  ocr: Record<string, unknown>;
}

export interface DifyChatResponse {
  answer: string;
  conversation_id?: string | null;
  app_type: string;
  response_mode: string;
  ocr_text_chars: number;
}

export interface LeaveAuditTableRow {
  key: string;
  task: LeaveAuditTask;
  result: LeaveAuditResult | null;
  request_id: string;
  leave_request_id: string;
  employee_name: string;
  leave_type: string;
  attachment_name: string;
  matched_attachment_type?: string;
  status: LeaveAuditStatus;
  risk_level?: string;
  verify_status?: string;
  updated_at: string;
}
