import type { AnalysisViewModel } from "@/types";
import { RiskBadge } from "./RiskBadge";

interface AnalysisPanelProps {
  analysis: AnalysisViewModel | null;
}

export function AnalysisPanel({ analysis }: AnalysisPanelProps) {
  if (!analysis) {
    return (
      <section className="panel">
        <h2>AnalysisPanel</h2>
        <p>暂无 analysis 数据。</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <h2>AnalysisPanel</h2>
          <p>组件层只消费 ViewModel，不直接读取 raw analyze response。</p>
        </div>
        <RiskBadge label={analysis.riskAction} tone="INFO" />
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
