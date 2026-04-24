import type { AnalysisResponse } from "@/types";
import { RiskBadge } from "./RiskBadge";

interface AnalysisPanelProps {
  analysis: AnalysisResponse["analysis"] | null;
}

function renderValue(value: unknown) {
  if (Array.isArray(value)) return value.length ? value.join(", ") : "[]";
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
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
          <p>只绑定前端需要解释的稳定字段。</p>
        </div>
        <RiskBadge label={analysis.risk.review_action} tone="INFO" />
      </div>

      <div className="summary-grid">
        <div className="summary-tile">
          <span className="summary-tile__label">doc_type</span>
          <strong>{analysis.doc_type}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">doc_type_confidence</span>
          <strong>{analysis.doc_type_confidence ?? "-"}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">attachment_label</span>
          <strong>{analysis.classification_evidence.attachment_label}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">attachment_confidence</span>
          <strong>{analysis.classification_evidence.attachment_confidence ?? "-"}</strong>
        </div>
      </div>

      <div className="info-card">
        <h3>关键词 / 分类证据</h3>
        <div className="tag-row">
          {analysis.classification_evidence.matched_keywords.length ? (
            analysis.classification_evidence.matched_keywords.map((item) => (
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
          {analysis.extracted_fields.map((field) => (
            <div key={field.name} className="field-table__row">
              <span>{field.name}</span>
              <span>{renderValue(field.value)}</span>
              <span>{field.confidence ?? "-"}</span>
              <span>{field.source ?? "-"}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="split-grid">
        <div className="info-card">
          <h3>validation</h3>
          <p>accepted: {String(analysis.validation.accepted)}</p>
          <ul>
            {analysis.validation.issues.map((issue) => (
              <li key={`${issue.code}-${issue.field_name ?? "none"}`}>
                <strong>{issue.code}</strong>: {issue.message}
              </li>
            ))}
          </ul>
        </div>
        <div className="info-card">
          <h3>review</h3>
          <p>action: {analysis.review.decision.action}</p>
          <ul>
            {analysis.review.warnings.map((warning) => (
              <li key={`${warning.code}-${warning.field_name ?? "none"}`}>
                <strong>{warning.code}</strong>: {warning.message}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
