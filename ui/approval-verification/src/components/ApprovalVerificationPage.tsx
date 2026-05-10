import { useEffect, useMemo, useRef, useState } from "react";
import type {
  ApprovalVerificationViewModel,
  AsyncStatus,
  DataSourceMode,
  MockScenario,
  RawAnalyzeResponse,
  RawVerifyResponse,
  VerifyStatus,
} from "@/types";
import { derivePilotDecisionUiState } from "./pilotDecisionState";
import { deriveStructuredFieldPresentation } from "./structuredFieldPresentation";
import { buildVerificationRunMeta, buildVerificationRunSummary } from "./verificationRunState";
import { resolveRequestId } from "@/adapters/requestTrace";

interface ApprovalVerificationPageProps {
  initialViewModel: ApprovalVerificationViewModel;
  mode: DataSourceMode;
  scenario: MockScenario;
  pageVersion: "default" | "v1";
  onModeChange: (mode: DataSourceMode) => void;
  onScenarioChange: (scenario: MockScenario) => void;
  onPageVersionChange: (version: "default" | "v1") => void;
  onAnalyze: (selectedFile: File | null) => Promise<RawAnalyzeResponse>;
  onVerify: (selectedFile: File | null) => Promise<RawVerifyResponse>;
  buildNextViewModel: (input: {
    rawAnalyzeResponse?: RawAnalyzeResponse;
    rawVerifyResponse?: RawVerifyResponse;
  }) => ApprovalVerificationViewModel;
}

function getImageSelectionError(file: File): string | null {
  if (!file.type.startsWith("image/")) {
    return "当前仅支持 image/*，暂不支持 PDF 或其他文件类型。";
  }
  return null;
}

function normalizeAnalysisAction(action: string): "PASS" | "REVIEW" | "REJECT" {
  const normalized = action.trim().toUpperCase();
  if (normalized === "AUTO_ACCEPT" || normalized === "PASS") return "PASS";
  if (normalized === "REJECT") return "REJECT";
  return "REVIEW";
}

function buildInconsistencyMessage(analysisAction: string, verifyStatus: VerifyStatus): string | null {
  const normalizedAnalysisAction = normalizeAnalysisAction(analysisAction);
  if (normalizedAnalysisAction === verifyStatus) {
    return null;
  }
  return "系统识别提示与业务核验结论不一致，建议优先按业务核验结论处理，并补充人工复核材料风险。";
}

function getStatusTone(status: string): "pass" | "review" | "reject" {
  const normalized = status.toUpperCase();
  if (normalized === "PASS" || normalized === "LOW") return "pass";
  if (normalized === "REJECT" || normalized === "HIGH") return "reject";
  return "review";
}

function getRiskLabel(level: string): string {
  const normalized = level.toUpperCase();
  if (normalized === "LOW") return "低风险";
  if (normalized === "HIGH") return "高风险";
  return "中风险";
}

function getBusinessStatusLabel(status: VerifyStatus): string {
  if (status === "PASS") return "通过";
  if (status === "REJECT") return "驳回";
  return "人工复核";
}

function getDecisionAdvice(status: VerifyStatus): string {
  if (status === "PASS") return "建议通过";
  if (status === "REJECT") return "建议驳回";
  return "建议人工复核";
}

function getDecisionSubtitle(status: VerifyStatus): string {
  if (status === "PASS") return "材料满足当前审批要求，可直接完成审批。";
  if (status === "REJECT") return "材料存在关键问题，建议驳回或退回补正。";
  return "材料存在待确认风险，建议先转人工复核。";
}

function getAttachmentTypeLabel(viewModel: ApprovalVerificationViewModel): string {
  const normalized = `${viewModel.analysis.attachmentLabel}|${viewModel.analysis.docType}`.toLowerCase();
  if (normalized.includes("medical_certificate") || normalized.includes("diagnosis_proof")) {
    return "诊断证明";
  }
  if (normalized.includes("marriage_certificate")) {
    return "婚姻证明材料";
  }
  return "请假证明材料";
}

function getApprovalConclusionText(viewModel: ApprovalVerificationViewModel): string {
  const attachmentLabel = getAttachmentTypeLabel(viewModel);
  if (viewModel.verification.verifyStatus === "PASS") {
    return `材料类型：${attachmentLabel}（符合要求）`;
  }
  if (viewModel.verification.verifyStatus === "REJECT") {
    return `材料类型：${attachmentLabel}（不符合要求）`;
  }
  return `材料类型：${attachmentLabel}（建议补充核验）`;
}

function formatFieldLabel(name: string): string {
  const labels: Record<string, string> = {
    patient_name: "姓名",
    rest_start_date: "休息开始日期",
    rest_end_date: "休息结束日期",
    rest_days: "休息天数",
    diagnosis: "诊断/描述",
    physician_name: "医生",
    issue_date: "开具日期",
    certificate_title: "证明标题",
    hospital_name: "医院",
    department: "科室",
    advice: "建议",
  };
  return labels[name] ?? name;
}

function mapRiskMessage(message: string): string {
  const normalized = message.trim();
  const mappings: Record<string, string> = {
    missing_hospital_name: "未识别到医院信息",
    "missing hospital_name": "未识别到医院信息",
    missing_diagnosis: "未识别到诊断信息",
    "missing diagnosis": "未识别到诊断信息",
    missing_issue_date: "未识别到开具日期",
    "missing issue_date": "未识别到开具日期",
    "missing diagnosis certificate title": "未识别到诊断证明标题",
    missing_certificate_title: "未识别到证明标题",
    "missing certificate_title": "未识别到证明标题",
    missing_registration_authority: "未识别到登记机关信息",
    "missing registration_authority": "未识别到登记机关信息",
    missing_seal: "未识别到盖章信息",
    "missing seal": "未识别到盖章信息",
    weak_sick_note_signal: "材料疑似非标准病假证明",
    not_sick_note_like: "材料不符合病假证明特征",
    "related person does not match": "材料人员信息与申请人不一致",
    "related person does not match extracted document relationship party": "材料人员信息与申请人不一致",
  };
  return mappings[normalized] ?? normalized;
}

function extractFieldValue(viewModel: ApprovalVerificationViewModel, fieldName: string): string {
  const field = viewModel.analysis.extractedFields.find((item) => item.name === fieldName);
  if (!field) return "-";
  if (Array.isArray(field.value)) {
    return field.value.length ? field.value.join("、") : "-";
  }
  if (typeof field.value === "boolean") {
    return field.value ? "是" : "否";
  }
  return field.displayValue || "-";
}

function buildStructuredRows(viewModel: ApprovalVerificationViewModel) {
  return [
    { label: "姓名", value: extractFieldValue(viewModel, "patient_name") },
    { label: "休息开始日期", value: extractFieldValue(viewModel, "rest_start_date") },
    { label: "休息结束日期", value: extractFieldValue(viewModel, "rest_end_date") },
    { label: "休息天数", value: extractFieldValue(viewModel, "rest_days") },
    { label: "诊断/描述", value: extractFieldValue(viewModel, "diagnosis") },
    { label: "医生", value: extractFieldValue(viewModel, "physician_name") },
    { label: "开具日期", value: extractFieldValue(viewModel, "issue_date") },
    { label: "材料类型", value: getAttachmentTypeLabel(viewModel) },
  ];
}

function buildReasonCards(viewModel: ApprovalVerificationViewModel) {
  const applicant = viewModel.requestHeader.applicantName;
  const patientName = extractFieldValue(viewModel, "patient_name");
  const startDate = extractFieldValue(viewModel, "rest_start_date");
  const endDate = extractFieldValue(viewModel, "rest_end_date");
  const hasSeal = extractFieldValue(viewModel, "seal_present") === "是";

  return [
    {
      title: "申请人是否一致",
      value: applicant === patientName ? "一致" : "需人工确认",
      detail: `材料姓名：${patientName}`,
      tone: applicant === patientName ? "pass" : "review",
    },
    {
      title: "请假日期是否覆盖",
      value: `${startDate} - ${endDate}`,
      detail: `申请区间：${viewModel.requestHeader.leaveDateRange}`,
      tone: viewModel.verification.verifyStatus === "PASS" ? "pass" : "review",
    },
    {
      title: "材料类型是否匹配",
      value: getAttachmentTypeLabel(viewModel),
      detail: viewModel.verification.verifyStatus === "PASS" ? "与申请类型匹配" : "建议结合申请类型再次确认",
      tone: viewModel.verification.verifyStatus === "REJECT" ? "reject" : "pass",
    },
    {
      title: "关键盖章是否存在",
      value: hasSeal ? "已检测到" : "未明确检测到",
      detail: hasSeal ? "可作为有效凭证继续审批" : "建议人工查看材料原件",
      tone: hasSeal ? "pass" : "review",
    },
  ];
}

function computeConfidence(viewModel: ApprovalVerificationViewModel): number {
  const passRatio = viewModel.verification.ruleResults.length
    ? viewModel.verification.ruleResults.filter((item) => item.passed).length / viewModel.verification.ruleResults.length
    : 1;
  const base = Math.round((viewModel.analysis.docTypeConfidence ?? 0.7) * 100);
  const weighted = Math.round(base * 0.55 + passRatio * 35 + (viewModel.verification.verifyStatus === "PASS" ? 10 : 0));
  return Math.max(41, Math.min(98, weighted));
}

function buildRiskItems(viewModel: ApprovalVerificationViewModel, inconsistencyMessage: string | null) {
  const items: Array<{
    title: string;
    action: string;
    detail: string;
    tone: "pass" | "review" | "reject";
  }> = [];

  items.push({
    title: "风险来源分类",
    action: `${viewModel.analysis.riskCategory.label}：${getRiskLabel(viewModel.analysis.riskCategory.level)}；${viewModel.verification.riskCategory.label}：${getRiskLabel(viewModel.verification.riskCategory.level)}。`,
    detail: `${viewModel.analysis.riskCategory.summary} ${viewModel.verification.riskCategory.summary}`,
    tone: viewModel.verification.verifyStatus === "REJECT" ? "reject" : viewModel.verification.verifyStatus === "PASS" ? "pass" : "review",
  });

  if (inconsistencyMessage) {
    items.push({
      title: "系统判断与业务结论存在分歧",
      action: "优先按当前业务核验结论处理，并复看原始材料后再决定是否通过。",
      detail: inconsistencyMessage,
      tone: "review",
    });
  }

  if (viewModel.verification.reviewReasonHint) {
    items.push({
      title: "材料仍未达到自动通过标准",
      action: viewModel.verification.reviewReasonHint,
      detail: "当前业务字段与结构化结果已基本对齐，但系统仍保留人工复核门槛。",
      tone: "review",
    });
  }

  viewModel.verification.explainabilityGroups.forEach((group) => {
    items.push({
      title: `Explainability · ${group.label}`,
      action: group.items[0] ?? "-",
      detail: group.items.slice(1).join("；") || "用于补充说明当前复核来源。",
      tone: "review",
    });
  });

  viewModel.verification.warnings.forEach((warning) => {
    items.push({
      title: mapRiskMessage(warning),
      action: viewModel.verification.verifyStatus === "PASS" ? "建议保留审批备注后通过。" : "建议转人工复核，确认是否需要补充材料。",
      detail: "请结合原始材料和申请单信息做最终判断。",
      tone: viewModel.verification.verifyStatus === "PASS" ? "pass" : "review",
    });
  });

  viewModel.analysis.validationIssues.forEach((issue) => {
    items.push({
      title: mapRiskMessage(issue.message),
      action: viewModel.verification.verifyStatus === "REJECT" ? "建议驳回或退回申请人补正后再提交。" : "建议重点查看原始材料对应位置，确认是否影响审批。",
      detail: "该项提示仅作为风险提醒，请以审批结论和材料内容为准。",
      tone: viewModel.verification.verifyStatus === "REJECT" ? "reject" : "review",
    });
  });

  if (!items.length) {
    items.push({
      title: "当前未发现明显审批风险",
      action: "可按照建议动作直接处理。",
      detail: "如需更谨慎，可继续查看结构化字段和原始材料。",
      tone: "pass",
    });
  }

  return items.slice(0, 4);
}

export function ApprovalVerificationPage({
  initialViewModel,
  mode,
  scenario,
  pageVersion,
  onModeChange,
  onScenarioChange,
  onPageVersionChange,
  onAnalyze,
  onVerify,
  buildNextViewModel,
}: ApprovalVerificationPageProps) {
  const [viewModel, setViewModel] = useState<ApprovalVerificationViewModel>(initialViewModel);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadInputError, setUploadInputError] = useState<string | null>(null);
  const [analyzeStatus, setAnalyzeStatus] = useState<AsyncStatus>("success");
  const [verifyStatus, setVerifyStatus] = useState<AsyncStatus>("success");
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [displayRequestId, setDisplayRequestId] = useState(initialViewModel.requestHeader.requestId);
  const [latestVerifyStartedAt, setLatestVerifyStartedAt] = useState<Date | null>(null);
  const [latestVerifyCompletedAt, setLatestVerifyCompletedAt] = useState<Date | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setViewModel(initialViewModel);
    setSelectedFile(null);
    setPreviewUrl(null);
    setUploadInputError(null);
    setAnalyzeStatus("success");
    setVerifyStatus("success");
    setAnalyzeError(null);
    setVerifyError(null);
    setDisplayRequestId(initialViewModel.requestHeader.requestId);
    setLatestVerifyStartedAt(null);
    setLatestVerifyCompletedAt(null);
  }, [initialViewModel]);

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      return undefined;
    }
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedFile]);

  const inconsistencyMessage = useMemo(
    () => buildInconsistencyMessage(viewModel.analysis.reviewAction, viewModel.verification.verifyStatus),
    [viewModel.analysis.reviewAction, viewModel.verification.verifyStatus],
  );

  const structuredRows = useMemo(() => buildStructuredRows(viewModel), [viewModel]);
  const reasonCards = useMemo(() => buildReasonCards(viewModel), [viewModel]);
  const verifyRunMeta = useMemo(() => buildVerificationRunMeta({
    verifyStatus,
    latestStartedAt: latestVerifyStartedAt,
    latestCompletedAt: latestVerifyCompletedAt,
  }), [verifyStatus, latestVerifyStartedAt, latestVerifyCompletedAt]);
  const timelineItems = verifyRunMeta.timelineItems;
  const confidence = useMemo(() => computeConfidence(viewModel), [viewModel]);
  const riskItems = useMemo(() => buildRiskItems(viewModel, inconsistencyMessage), [viewModel, inconsistencyMessage]);

  const uploadedFilename = selectedFile?.name ?? viewModel.attachments[0]?.filename ?? "-";
  const selectedAttachmentStatus = viewModel.verification.verifyStatus;
  const decisionUiState = derivePilotDecisionUiState({
    verifyStatus: viewModel.verification.verifyStatus,
    verifyError,
  });
  const suggestionTone = decisionUiState.suggestionTone;
  const analysisTone = getStatusTone(viewModel.analysis.reviewAction);
  const decisionAdvice = decisionUiState.decisionAdvice;
  const decisionSubtitle = decisionUiState.decisionSubtitle;
  const approvalConclusionText = getApprovalConclusionText(viewModel);
  const attachmentTypeLabel = getAttachmentTypeLabel(viewModel);
  const structuredFieldPresentation = useMemo(() => deriveStructuredFieldPresentation(viewModel), [viewModel]);
  const verificationRunSummary = useMemo(() => buildVerificationRunSummary({
    filename: uploadedFilename,
    backendStatus: viewModel.verification.summaryMessage,
    requestId: displayRequestId,
    completedAtLabel: verifyRunMeta.completedAtLabel,
  }), [uploadedFilename, viewModel.verification.summaryMessage, displayRequestId, verifyRunMeta.completedAtLabel]);

  function handleFileChange(file: File | null) {
    if (!file) {
      setSelectedFile(null);
      setUploadInputError(null);
      return;
    }
    const error = getImageSelectionError(file);
    if (error) {
      setSelectedFile(null);
      setUploadInputError(error);
      return;
    }
    setSelectedFile(file);
    setUploadInputError(null);
  }

  async function handleAnalyze() {
    if (mode === "real" && uploadInputError) {
      setAnalyzeStatus("error");
      setAnalyzeError(uploadInputError);
      return;
    }
    setAnalyzeStatus("loading");
    setAnalyzeError(null);
    let rawAnalyzeResponse: RawAnalyzeResponse | null = null;
    try {
      rawAnalyzeResponse = await onAnalyze(selectedFile);
      setViewModel(buildNextViewModel({ rawAnalyzeResponse }));
      setDisplayRequestId(rawAnalyzeResponse.request_id);
      setAnalyzeStatus("success");
    } catch (error) {
      const tracedRequestId = resolveRequestId({ response: rawAnalyzeResponse, error });
      if (tracedRequestId) {
        setDisplayRequestId(tracedRequestId);
      }
      setAnalyzeStatus("error");
      setAnalyzeError(error instanceof Error ? error.message : "analyze failed");
    }
  }

  async function handleVerify() {
    if (mode === "real" && uploadInputError) {
      setVerifyStatus("error");
      setVerifyError(uploadInputError);
      return;
    }
    setVerifyStatus("loading");
    setVerifyError(null);
    setLatestVerifyStartedAt(new Date());
    setLatestVerifyCompletedAt(null);
    let rawVerifyResponse: RawVerifyResponse | null = null;
    try {
      rawVerifyResponse = await onVerify(selectedFile);
      setViewModel(buildNextViewModel({ rawVerifyResponse }));
      setDisplayRequestId(rawVerifyResponse.request_id);
      setLatestVerifyCompletedAt(new Date());
      setVerifyStatus("success");
    } catch (error) {
      const tracedRequestId = resolveRequestId({ response: rawVerifyResponse, error });
      if (tracedRequestId) {
        setDisplayRequestId(tracedRequestId);
      }
      setLatestVerifyCompletedAt(new Date());
      setVerifyStatus("error");
      setVerifyError(error instanceof Error ? error.message : "verify failed");
    }
  }

  return (
    <div className="glf-shell">
      <aside className="glf-sidebar">
        <div className="glf-brand">
          <div className="glf-brand__mark">核</div>
          <div>
            <strong>请假单据核验</strong>
            <p>Leave Document Verification</p>
          </div>
        </div>

        <nav className="glf-nav">
          {[
            ["工作台", null],
            ["单据核验", "active"],
            ["待我审批", "12"],
            ["我已审批", null],
            ["我的申请", null],
            ["统计报表", null],
            ["系统设置", null],
          ].map(([label, badge]) => (
            <button key={label} type="button" className={`glf-nav__item${badge === "active" ? " glf-nav__item--active" : ""}`}>
              <span>{label}</span>
              {badge && badge !== "active" ? <span className="glf-nav__badge">{badge}</span> : null}
            </button>
          ))}
        </nav>

        <div className="glf-sidebar-card">
          <p className="glf-sidebar-card__title">当前建议动作</p>
          <strong className={`glf-sidebar-card__decision glf-sidebar-card__decision--${suggestionTone}`}>{decisionAdvice}</strong>
          <p className="muted">{decisionSubtitle}</p>
        </div>
      </aside>

      <main className="glf-main">
        <header className="glf-header">
          <div>
            <p className="glf-header__eyebrow">事务 / 单据核验详情</p>
            <h1>审批材料核验工作台</h1>
            <p className="glf-header__summary">先看建议动作，再核对审批材料，最后确认风险提示。</p>
          </div>
          <div className="glf-header__meta">
            <span className="glf-chip">Request ID: {displayRequestId}</span>
            <div className="glf-usercard">
              <div className="glf-usercard__avatar">HR</div>
              <div>
                <strong>HR-Approver-01</strong>
                <p>审批人</p>
              </div>
            </div>
            <details className="glf-debug-menu">
              <summary>调试入口</summary>
              <div className="glf-debug-menu__panel">
                <div className="glf-debug-menu__group">
                  <span>页面</span>
                  <button type="button" className={pageVersion === "default" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onPageVersionChange("default")}>当前页</button>
                  <button type="button" className="scenario-button" onClick={() => onPageVersionChange("v1")}>打开 V1</button>
                </div>
                <div className="glf-debug-menu__group">
                  <span>数据源</span>
                  <button type="button" className={mode === "mock" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onModeChange("mock")}>Mock</button>
                  <button type="button" className={mode === "real" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onModeChange("real")}>Real</button>
                </div>
                <div className="glf-debug-menu__group">
                  <span>场景</span>
                  <button type="button" className={scenario === "pass" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onScenarioChange("pass")}>通过</button>
                  <button type="button" className={scenario === "review" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onScenarioChange("review")}>复核</button>
                </div>
              </div>
            </details>
          </div>
        </header>

        <section className="glf-primary-grid">
          <div className="glf-panel glf-panel--document glf-panel--hero-document">
            <div className="glf-section-header glf-section-header--stacked-mobile">
              <div>
                <h3>审批材料（必须核验）</h3>
                <p>审批前请先核对材料内容、姓名、日期与盖章信息。</p>
              </div>
              <button type="button" className="glf-link-button" onClick={() => fileInputRef.current?.click()}>选择图片</button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden-file-input"
              onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)}
            />
            <div className="glf-upload-meta">
              <span>当前文件：{uploadedFilename}</span>
              <span>材料形式：{selectedFile ? "上传图片附件" : "示例图片附件"}</span>
              <span>当前建议：{decisionAdvice}</span>
            </div>
            {uploadInputError ? <p className="upload-error">{uploadInputError}</p> : null}
            <div className="glf-document-canvas glf-document-canvas--hero">
              {previewUrl ? (
                <img src={previewUrl} alt={uploadedFilename} className="glf-document-image" />
              ) : (
                <div className="glf-demo-paper">
                  <p className="glf-demo-paper__title">示例材料</p>
                  <p>申请人：{viewModel.requestHeader.applicantName}</p>
                  <p>材料类型：{attachmentTypeLabel}</p>
                  <p>日期信息：{extractFieldValue(viewModel, "rest_start_date")} - {extractFieldValue(viewModel, "rest_end_date")}</p>
                  <p>开具日期：{extractFieldValue(viewModel, "issue_date")}</p>
                  <p>说明：请以上传附件预览为准</p>
                  <div className="glf-demo-paper__seal">章</div>
                </div>
              )}
            </div>
            <div className="glf-thumbnail-strip">
              <span className="glf-thumbnail-strip__thumb">1</span>
              <span>1/1</span>
              <span>当前结论：{getBusinessStatusLabel(selectedAttachmentStatus)}</span>
            </div>
          </div>

          <div className="glf-primary-side">
            <section className="glf-summary-card glf-summary-card--action-first">
              <div className="glf-summary-card__conclusion">
                <div className={`glf-summary-card__icon glf-summary-card__icon--${suggestionTone}`}>
                  {viewModel.verification.verifyStatus === "PASS" ? "✓" : viewModel.verification.verifyStatus === "REJECT" ? "!" : "?"}
                </div>
                <div>
                  <p className="glf-summary-card__label">建议动作</p>
                  <h2>{decisionAdvice}</h2>
                  <p className="glf-summary-card__subtext">{decisionSubtitle}</p>
                </div>
              </div>
              <div className="glf-summary-card__metric">
                <span>审批结论</span>
                <strong>{approvalConclusionText}</strong>
                <small>{getRiskLabel(viewModel.verification.riskLevel)}</small>
              </div>
              <div className="glf-summary-card__subtext" style={{ display: "flex", flexWrap: "wrap", gap: "8px 14px" }}>
                <span>本次核验摘要</span>
                {verificationRunSummary.map((item) => <span key={item}>{item}</span>)}
              </div>
              <div className="glf-summary-card__metric">
                <span>人工处理建议</span>
                <strong>{viewModel.verification.verifyStatus === "REVIEW" ? "需要人工复核" : viewModel.verification.verifyStatus === "REJECT" ? "建议退回补正" : "可直接处理"}</strong>
                <small>请结合材料原件做最终审批</small>
              </div>
              <div className="glf-summary-card__metric">
                <span>核验把握度</span>
                <strong>{confidence}%</strong>
                <small>仅供审批人参考</small>
              </div>
            </section>

            <section className="glf-action-row glf-action-row--decision-first">
              <button type="button" className={`glf-decision-btn glf-decision-btn--pass${suggestionTone === "pass" ? " glf-decision-btn--active" : ""}`}>通过</button>
              <button type="button" className={`glf-decision-btn glf-decision-btn--review${suggestionTone === "review" ? " glf-decision-btn--active" : ""}`}>转人工复核</button>
              <button type="button" className={`glf-decision-btn glf-decision-btn--reject${suggestionTone === "reject" ? " glf-decision-btn--active" : ""}`}>驳回</button>
            </section>

            <section className="glf-ops-row">
              <button type="button" className="action-button" onClick={handleVerify} disabled={verifyStatus === "loading"}>{verifyStatus === "loading" ? "核验中..." : "运行核验"}</button>
            </section>
          </div>
        </section>

        <section className="glf-secondary-grid">
          <div className="glf-reasons glf-panel">
            <div className="glf-section-header">
              <h3>为什么建议这样处理</h3>
              <p>只保留审批时最需要确认的几项依据。</p>
            </div>
            <div className="glf-reason-grid glf-reason-grid--compact">
              {reasonCards.map((card) => (
                <article key={card.title} className={`glf-reason-card glf-reason-card--${card.tone}`}>
                  <span className="glf-reason-card__title">{card.title}</span>
                  <strong>{card.value}</strong>
                  <small>{card.detail}</small>
                </article>
              ))}
            </div>
          </div>

          <div className="glf-panel glf-panel--risk">
            <div className="glf-section-header">
              <h3>风险提示与建议动作</h3>
              <span className={`badge badge--${suggestionTone}`}>{decisionAdvice}</span>
            </div>
            <div className="glf-warning-stack">
              {riskItems.map((item, index) => (
                <article key={`${item.title}-${index}`} className={`glf-warning-card glf-warning-card--${item.tone}`}>
                  <span className="glf-warning-card__eyebrow">问题</span>
                  <strong>{item.title}</strong>
                  <span className="glf-warning-card__eyebrow">建议动作</span>
                  <p className="glf-warning-card__action">{item.action}</p>
                  <p>{item.detail}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="glf-panel glf-panel--structured">
          <div className="glf-section-header">
            <div>
              <h3>结构化信息（审批辅助）</h3>
              <p>用于快速核对关键字段，如需更多技术细节请展开下方调试信息。</p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              {structuredFieldPresentation.badgeText ? <span className={`badge badge--${structuredFieldPresentation.emphasisTone}`}>{structuredFieldPresentation.badgeText}</span> : null}
              <button type="button" className="glf-link-button">查看全部字段</button>
            </div>
          </div>
          <div className={`glf-warning-card glf-warning-card--${structuredFieldPresentation.emphasisTone}`}>
            {structuredFieldPresentation.reviewHint ? (
              <>
                <span className="glf-warning-card__eyebrow">需复核提示</span>
                <p className="glf-warning-card__action">{structuredFieldPresentation.reviewHint}</p>
              </>
            ) : null}
            <p>{structuredFieldPresentation.contextNotice}</p>
          </div>
          <dl className="glf-kv-list glf-kv-list--two-column">
            {structuredRows.map((row) => (
              <div key={row.label} className="glf-kv-list__row">
                <dt>{row.label}</dt>
                <dd>{row.value}</dd>
              </div>
            ))}
          </dl>
        </section>

        <details className="glf-collapsible-panel">
          <summary>展开调试详情（分析摘要 / 核验状态 / 处理时间线）</summary>
          <div className="glf-collapsible-panel__content">
            <div className="glf-content-grid glf-content-grid--collapsed-detail">
              <div className="glf-panel">
                <div className="glf-section-header">
                  <h3>核验状态摘要</h3>
                  <span className={`badge badge--${getStatusTone(viewModel.verification.verifyStatus)}`}>{getBusinessStatusLabel(viewModel.verification.verifyStatus)}</span>
                </div>
                <dl className="glf-stat-list">
                  <div><dt>当前状态</dt><dd className={`glf-stat-list__status glf-stat-list__status--${suggestionTone}`}>{getBusinessStatusLabel(viewModel.verification.verifyStatus)}</dd></div>
                  <div><dt>风险等级</dt><dd className={`glf-stat-list__status glf-stat-list__status--${getStatusTone(viewModel.verification.riskLevel)}`}>{getRiskLabel(viewModel.verification.riskLevel)}</dd></div>
                  <div><dt>后端返回状态</dt><dd>{viewModel.verification.summaryMessage}</dd></div>
                  <div><dt>本次文件名</dt><dd>{uploadedFilename}</dd></div>
                  <div><dt>本次 Request ID</dt><dd>{displayRequestId}</dd></div>
                  <div><dt>处理进度</dt><dd>{verifyRunMeta.statusText}</dd></div>
                  <div><dt>校验时间</dt><dd>{verifyRunMeta.completedAtLabel}</dd></div>
                </dl>
              </div>

              <div className="glf-panel">
                <div className="glf-section-header">
                  <h3>分析摘要</h3>
                  <span className={`badge badge--${analysisTone}`}>{getBusinessStatusLabel(normalizeAnalysisAction(viewModel.analysis.reviewAction))}</span>
                </div>
                <dl className="glf-stat-list">
                  <div><dt>识别建议</dt><dd>{getBusinessStatusLabel(normalizeAnalysisAction(viewModel.analysis.reviewAction))}</dd></div>
                  <div><dt>材料类别</dt><dd>{attachmentTypeLabel}</dd></div>
                  <div><dt>识别完整度</dt><dd>{confidence >= 85 ? "较完整" : confidence >= 65 ? "基本完整" : "需人工补充确认"}</dd></div>
                  <div><dt>风险提示数</dt><dd>{viewModel.analysis.validationIssues.length}</dd></div>
                  <div><dt>辅助说明</dt><dd>仅用于辅助审批，不直接替代人工判断</dd></div>
                </dl>
              </div>

              <div className="glf-panel glf-panel--timeline-detail">
                <div className="glf-section-header">
                  <h3>处理流程时间线</h3>
                  <span className="badge badge--info">调试信息</span>
                </div>
                <div className="glf-timeline">
                  {timelineItems.map((item) => (
                    <div key={item.label} className="glf-timeline__item">
                      <span className={`glf-timeline__dot glf-timeline__dot--${item.tone}`}></span>
                      <div>
                        <strong>{item.label}</strong>
                        <p>{item.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </details>

        {(analyzeError || verifyError || decisionUiState.staleResultWarning) ? (
          <div className="glf-error-banner">
            {analyzeError ? <p>分析错误：{analyzeError}</p> : null}
            {verifyError ? <p>核验错误：{verifyError}</p> : null}
            {decisionUiState.staleResultWarning ? <p>{decisionUiState.staleResultWarning}</p> : null}
          </div>
        ) : null}
      </main>
    </div>
  );
}
