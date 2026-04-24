import type { AnalysisViewModel, AsyncStatus } from "@/types";
import { RiskBadge } from "./RiskBadge";

interface AnalysisPanelProps {
  analysis: AnalysisViewModel | null;
  analyzeStatus: AsyncStatus;
  errorMessage?: string | null;
}

function getAnalysisRiskLevel(riskScore: number): "LOW" | "MEDIUM" | "HIGH" {
  if (riskScore >= 0.75) return "HIGH";
  if (riskScore >= 0.35) return "MEDIUM";
  return "LOW";
}

export function AnalysisPanel({ analysis, analyzeStatus, errorMessage }: AnalysisPanelProps) {
  if (!analysis) {
    return (
      <section className="panel">
        <h2>AnalysisPanel</h2>
        <p>暂无 analysis 数据。</p>
      </section>
    );
  }

  const riskLevel = getAnalysisRiskLevel(analysis.riskScore);

  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <h2>AnalysisPanel</h2>
          <p>组件层只消费 ViewModel，不直接读取 raw analyze response。</p>
        </div>
        <RiskBadge label={analysis.riskAction} tone="INFO" />
      </div>

      {analyzeStatus === "error" ? (
        <div className="panel-alert panel-alert--error">
          <strong>Analysis request failed.</strong>
          <p>{errorMessage ?? "analyze 调用失败。"}</p>
          <p>当前显示的是上一次结果。</p>
        </div>
      ) : null}

      <div className="info-card info-card--emphasis">
        <div className="section-heading-row">
          <h3>Analysis suggestion</h3>
          <div className="status-stack">
            <RiskBadge label={analysis.reviewAction} tone="INFO" />
            <RiskBadge label={riskLevel} tone={riskLevel} />
          </div>
        </div>
        <p className="muted">这是识别 / 质量 / 解析层建议，不等同于右侧业务规则核验结论。</p>
        <div className="summary-grid">
          <div className="summary-tile">
            <span className="summary-tile__label">analysis.review.action</span>
            <strong>{analysis.reviewAction}</strong>
          </div>
          <div className="summary-tile">
            <span className="summary-tile__label">analysis.risk.level</span>
            <strong>{riskLevel}</strong>
          </div>
          <div className="summary-tile">
            <span className="summary-tile__label">analysis.risk.score</span>
            <strong>{analysis.riskScore}</strong>
          </div>
          <div className="summary-tile">
            <span className="summary-tile__label">review_recommended</span>
            <strong>{String(analysis.reviewRecommended)}</strong>
          </div>
        </div>
      </div>

      <div className="summary-grid">
        <div className="summary-tile">
          <span className="summary-tile__label">doc_type</span>
          <strong>{analysis.docType}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">doc_type_confidence</span>
          <strong>{analysis.docTypeConfidence ?? "-"}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">attachment_label</span>
          <strong>{analysis.attachmentLabel}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">attachment_confidence</span>
          <strong>{analysis.attachmentConfidence ?? "-"}</strong>
        </div>
      </div>

      <div className="info-card">
        <h3>关键词 / 分类证据</h3>
        <div className="tag-row">
          {analysis.matchedKeywords.length ? (
            analysis.matchedKeywords.map((item) => (
              <span key={item} className="tag">{item}</span>
            ))
          ) : (
            <span className="muted">当前 mock 没有 OCR 关键词命中，展示 fallback label。</span>
          )}
        </div>
      </div>

      <div className="info-card">
        <h3>extracted_fields</h3>
        <div className="field-table">
          <div className="field-table__head">
            <span>field</span>
            <span>value</span>
            <span>confidence</span>
            <span>source</span>
          </div>
          {analysis.extractedFields.map((field) => (
            <div key={field.name} className="field-table__row">
              <span>{field.name}</span>
              <span>{field.displayValue}</span>
              <span>{field.confidence ?? "-"}</span>
              <span>{field.source ?? "-"}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="split-grid">
        <div className="info-card">
          <h3>validation</h3>
          <p>accepted: {String(analysis.validationAccepted)}</p>
          <ul>
            {analysis.validationIssues.map((issue) => (
              <li key={`${issue.code}-${issue.fieldName ?? "none"}`}>
                <strong>{issue.code}</strong>: {issue.message}
              </li>
            ))}
          </ul>
        </div>
        <div className="info-card">
          <h3>review</h3>
          <p>action: {analysis.reviewAction}</p>
          <ul>
            {analysis.reviewWarnings.map((warning) => (
              <li key={`${warning.code}-${warning.fieldName ?? "none"}`}>
                <strong>{warning.code}</strong>: {warning.message}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
