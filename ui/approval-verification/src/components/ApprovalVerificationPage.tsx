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
  return `识别分析建议 (${analysisAction}) 与业务核验结论 (${verifyStatus}) 不一致，请以业务核验结论为主，并人工复核分析风险。`;
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

function getDecisionAdvice(status: VerifyStatus): string {
  if (status === "PASS") return "可直接通过审批";
  if (status === "REJECT") return "建议驳回或退回补正";
  return "建议转人工复核";
}

function getDecisionText(status: VerifyStatus): string {
  if (status === "PASS") return "建议通过";
  if (status === "REJECT") return "建议驳回";
  return "建议复核";
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
    doc_type: "文档类型",
    certificate_title: "证明标题",
    hospital_name: "医院",
    department: "科室",
    advice: "建议",
  };
  return labels[name] ?? name;
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
    { label: "文档类型", value: `${viewModel.analysis.attachmentLabel} (${viewModel.analysis.docType})` },
  ];
}

function buildReasonCards(viewModel: ApprovalVerificationViewModel) {
  const applicant = viewModel.requestHeader.applicantName;
  const patientName = extractFieldValue(viewModel, "patient_name");
  const startDate = extractFieldValue(viewModel, "rest_start_date");
  const endDate = extractFieldValue(viewModel, "rest_end_date");
  const hasSeal = extractFieldValue(viewModel, "seal_present") === "是";
  const warningText = viewModel.verification.warnings[0] ?? "未发现冲突信息";

  return [
    {
      title: "姓名匹配",
      value: applicant === patientName ? "一致" : "需复核",
      detail: patientName,
      tone: applicant === patientName ? "pass" : "review",
    },
    {
      title: "日期有效",
      value: `${startDate} - ${endDate}`,
      detail: viewModel.requestHeader.leaveDateRange,
      tone: viewModel.verification.verifyStatus === "PASS" ? "pass" : "review",
    },
    {
      title: "文档类型",
      value: viewModel.analysis.attachmentLabel,
      detail: viewModel.analysis.docType,
      tone: viewModel.verification.verifyStatus === "REJECT" ? "reject" : "pass",
    },
    {
      title: "风险提示",
      value: hasSeal ? "已检测到盖章" : "未检测到医院盖章",
      detail: hasSeal ? "已通过" : "可接受",
      tone: hasSeal ? "pass" : "review",
    },
    {
      title: "其他校验",
      value: viewModel.verification.warnings.length ? warningText : "关键字段完整",
      detail: viewModel.verification.warnings.length ? "需人工关注" : "无冲突信息",
      tone: viewModel.verification.warnings.length ? "review" : "pass",
    },
  ];
}

function buildTimelineItems() {
  return [
    { label: "文档上传", time: "10:32:30", tone: "pass" },
    { label: "文档分析", time: "10:32:31", tone: "pass" },
    { label: "规则验证", time: "10:32:32", tone: "pass" },
    { label: "完成核验", time: "10:32:45", tone: "info" },
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
  const timelineItems = useMemo(() => buildTimelineItems(), []);
  const confidence = useMemo(() => computeConfidence(viewModel), [viewModel]);

  const uploadedFilename = selectedFile?.name ?? viewModel.attachments[0]?.filename ?? "-";
  const uploadedFileType = selectedFile?.type ?? viewModel.attachments[0]?.contentType ?? "-";
  const selectedAttachmentStatus = viewModel.verification.verifyStatus;
  const suggestionTone = getStatusTone(viewModel.verification.verifyStatus);
  const analysisTone = getStatusTone(viewModel.analysis.reviewAction);

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
    try {
      const rawAnalyzeResponse = await onAnalyze(selectedFile);
      setViewModel(buildNextViewModel({ rawAnalyzeResponse }));
      setAnalyzeStatus("success");
    } catch (error) {
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
    try {
      const rawVerifyResponse = await onVerify(selectedFile);
      setViewModel(buildNextViewModel({ rawVerifyResponse }));
      setVerifyStatus("success");
    } catch (error) {
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
          <p className="glf-sidebar-card__title">需要帮助？</p>
          <p className="muted">查看审批人 SOP 指南</p>
          <button type="button" className="glf-link-button">打开 SOP</button>
        </div>
      </aside>

      <main className="glf-main">
        <header className="glf-header">
          <div>
            <p className="glf-header__eyebrow">事务 / 单据核验详情</p>
            <h1>Leave Verification Dashboard</h1>
          </div>
          <div className="glf-header__meta">
            <span className="glf-chip">Request ID: {viewModel.requestHeader.requestId}</span>
            <span className="glf-chip">{mode === "real" ? "Real Adapter" : "Mock"}</span>
            <div className="glf-usercard">
              <div className="glf-usercard__avatar">HR</div>
              <div>
                <strong>HR-Approver-01</strong>
                <p>审批人</p>
              </div>
            </div>
          </div>
        </header>

        <section className="glf-controls">
          <div className="glf-controls__group">
            <span className="glf-controls__label">页面版本</span>
            <button type="button" className={pageVersion === "default" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onPageVersionChange("default")}>默认页</button>
            <button type="button" className={pageVersion === "v1" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onPageVersionChange("v1")}>V1</button>
          </div>
          <div className="glf-controls__group">
            <span className="glf-controls__label">数据源</span>
            <button type="button" className={mode === "mock" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onModeChange("mock")}>Mock mode</button>
            <button type="button" className={mode === "real" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onModeChange("real")}>Real adapter mode</button>
          </div>
          <div className="glf-controls__group">
            <span className="glf-controls__label">演示场景</span>
            <button type="button" className={scenario === "pass" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onScenarioChange("pass")}>PASS mock</button>
            <button type="button" className={scenario === "review" ? "scenario-button scenario-button--active" : "scenario-button"} onClick={() => onScenarioChange("review")}>REVIEW mock</button>
          </div>
        </section>

        <section className="glf-summary-card">
          <div className="glf-summary-card__conclusion">
            <div className={`glf-summary-card__icon glf-summary-card__icon--${suggestionTone}`}>
              {viewModel.verification.verifyStatus === "PASS" ? "✓" : viewModel.verification.verifyStatus === "REJECT" ? "!" : "?"}
            </div>
            <div>
              <p className="glf-summary-card__label">核验结论</p>
              <h2>{viewModel.verification.verifyStatus}</h2>
              <p className="glf-summary-card__subtext">{getDecisionText(viewModel.verification.verifyStatus)}</p>
            </div>
          </div>
          <div className="glf-summary-card__metric">
            <span>风险等级</span>
            <strong>{getRiskLabel(viewModel.verification.riskLevel)}</strong>
            <small>{viewModel.verification.riskLevel}</small>
          </div>
          <div className="glf-summary-card__metric">
            <span>置信度</span>
            <strong>{confidence}%</strong>
            <small>{viewModel.analysis.docTypeConfidence ? `analysis ${Math.round(viewModel.analysis.docTypeConfidence * 100)}%` : "derived"}</small>
          </div>
          <div className="glf-summary-card__metric">
            <span>处理建议</span>
            <strong>{getDecisionAdvice(viewModel.verification.verifyStatus)}</strong>
            <small>{viewModel.verification.summaryMessage}</small>
          </div>
        </section>

        <section className="glf-action-row">
          <button type="button" className="glf-decision-btn glf-decision-btn--pass">通过</button>
          <button type="button" className="glf-decision-btn glf-decision-btn--review">转人工复核</button>
          <button type="button" className="glf-decision-btn glf-decision-btn--reject">驳回</button>
          <div className="glf-action-row__spacer" />
          <button type="button" className="action-button" onClick={handleAnalyze} disabled={analyzeStatus === "loading"}>{analyzeStatus === "loading" ? "分析中..." : "运行分析"}</button>
          <button type="button" className="action-button action-button--secondary" onClick={handleVerify} disabled={verifyStatus === "loading"}>{verifyStatus === "loading" ? "核验中..." : "运行核验"}</button>
        </section>

        <section className="glf-reasons">
          <div className="glf-section-header">
            <h3>为什么是这个结论？</h3>
            <p>审批时优先看业务核验结论，再看触发原因。</p>
          </div>
          <div className="glf-reason-grid">
            {reasonCards.map((card) => (
              <article key={card.title} className={`glf-reason-card glf-reason-card--${card.tone}`}>
                <span className="glf-reason-card__title">{card.title}</span>
                <strong>{card.value}</strong>
                <small>{card.detail}</small>
              </article>
            ))}
          </div>
        </section>

        <section className="glf-content-grid">
          <div className="glf-panel glf-panel--document">
            <div className="glf-section-header">
              <h3>原始材料</h3>
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
              <span>类型：{uploadedFileType}</span>
              <span>状态：{selectedAttachmentStatus}</span>
            </div>
            {uploadInputError ? <p className="upload-error">{uploadInputError}</p> : null}
            <div className="glf-document-canvas">
              {previewUrl ? (
                <img src={previewUrl} alt={uploadedFilename} className="glf-document-image" />
              ) : (
                <div className="glf-demo-paper">
                  <p className="glf-demo-paper__title">SICK LEAVE DEMO</p>
                  <p>Patient: {viewModel.requestHeader.applicantName}</p>
                  <p>Rest: {extractFieldValue(viewModel, "rest_start_date")} - {extractFieldValue(viewModel, "rest_end_date")}</p>
                  <p>Days: {extractFieldValue(viewModel, "rest_days")}</p>
                  <p>Doctor: {extractFieldValue(viewModel, "physician_name")}</p>
                  <p>Date: {extractFieldValue(viewModel, "issue_date")}</p>
                  <div className="glf-demo-paper__seal">章</div>
                </div>
              )}
            </div>
            <div className="glf-thumbnail-strip">
              <span className="glf-thumbnail-strip__thumb">1</span>
              <span>1/1</span>
            </div>
          </div>

          <div className="glf-panel">
            <div className="glf-section-header">
              <h3>结构化信息（关键信息）</h3>
              <button type="button" className="glf-link-button">查看全部字段</button>
            </div>
            <dl className="glf-kv-list">
              {structuredRows.map((row) => (
                <div key={row.label} className="glf-kv-list__row">
                  <dt>{row.label}</dt>
                  <dd>{row.value}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="glf-panel">
            <div className="glf-section-header">
              <h3>验证结果</h3>
              <span className={`badge badge--${getStatusTone(viewModel.verification.verifyStatus)}`}>{viewModel.verification.verifyStatus}</span>
            </div>
            <dl className="glf-stat-list">
              <div><dt>验证状态</dt><dd className={`glf-stat-list__status glf-stat-list__status--${suggestionTone}`}>{viewModel.verification.verifyStatus}</dd></div>
              <div><dt>风险等级</dt><dd className={`glf-stat-list__status glf-stat-list__status--${getStatusTone(viewModel.verification.riskLevel)}`}>{viewModel.verification.riskLevel}</dd></div>
              <div><dt>置信度</dt><dd>{confidence}%</dd></div>
              <div><dt>验证耗时</dt><dd>{verifyStatus === "loading" ? "进行中" : mode === "real" ? "114 ms" : "114 ms"}</dd></div>
              <div><dt>校验时间</dt><dd>2025-05-06 10:32:45</dd></div>
            </dl>
          </div>

          <div className="glf-panel">
            <div className="glf-section-header">
              <h3>分析摘要</h3>
              <span className={`badge badge--${analysisTone}`}>{viewModel.analysis.reviewAction}</span>
            </div>
            <dl className="glf-stat-list">
              <div><dt>分析状态</dt><dd>{viewModel.analysis.reviewAction}</dd></div>
              <div><dt>文档类型</dt><dd>{viewModel.analysis.docType}</dd></div>
              <div><dt>分析耗时</dt><dd>{mode === "real" ? "802 ms" : "802 ms"}</dd></div>
              <div><dt>关键问题数</dt><dd>{viewModel.analysis.validationIssues.length}</dd></div>
              <div><dt>分析时间</dt><dd>2025-05-06 10:32:45</dd></div>
            </dl>
          </div>

          <div className="glf-panel">
            <div className="glf-section-header">
              <h3>风险提示详情</h3>
              {inconsistencyMessage ? <span className="badge badge--review">analysis ≠ verify</span> : null}
            </div>
            <div className="glf-warning-stack">
              <article className="glf-warning-card glf-warning-card--review">
                <strong>{viewModel.analysis.validationIssues[0]?.message ?? "未检测到明显问题"}</strong>
                <span>{viewModel.verification.verifyStatus === "PASS" ? "可接受" : "需处理"}</span>
                <p>{inconsistencyMessage ?? "材料内容完整，符合当前业务核验要求。"}</p>
              </article>
              <article className="glf-warning-card glf-warning-card--pass">
                <strong>{viewModel.verification.warnings[0] ?? "未发现冲突信息"}</strong>
                <p>未发现与请假信息冲突的内容。</p>
              </article>
            </div>
          </div>

          <div className="glf-panel">
            <div className="glf-section-header">
              <h3>处理流程时间线</h3>
              <span className="badge badge--info">实时概览</span>
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
        </section>

        <footer className="glf-footer-bar">
          <span>展开详细信息（原始分析结果 / 验证详情 / 字段明细）</span>
          <span>⌄</span>
        </footer>

        {(analyzeError || verifyError) ? (
          <div className="glf-error-banner">
            {analyzeError ? <p>分析错误：{analyzeError}</p> : null}
            {verifyError ? <p>核验错误：{verifyError}</p> : null}
          </div>
        ) : null}
      </main>
    </div>
  );
}
