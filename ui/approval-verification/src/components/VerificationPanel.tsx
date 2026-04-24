import type { VerificationResponse } from "@/types";
import { RiskBadge } from "./RiskBadge";
import { RuleResultList } from "./RuleResultList";

interface VerificationPanelProps {
  verification: VerificationResponse["verification"] | null;
}

export function VerificationPanel({ verification }: VerificationPanelProps) {
  if (!verification) {
    return (
      <section className="panel">
        <h2>VerificationPanel</h2>
        <p>暂无 verification 数据。</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <h2>VerificationPanel</h2>
          <p>优先展示 summary_message、risk_level、rule_results。</p>
        </div>
        <div className="status-stack">
          <RiskBadge label={verification.verify_status} tone={verification.verify_status} />
          <RiskBadge label={verification.risk_level} tone={verification.risk_level} />
        </div>
      </div>

      <div className="summary-grid">
        <div className="summary-tile">
          <span className="summary-tile__label">summary_message</span>
          <strong>{verification.summary_message}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">matched_attachment_type</span>
          <strong>{verification.matched_attachment_type}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">risk_score</span>
          <strong>{verification.risk_score}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">needs_manual_review</span>
          <strong>{String(verification.needs_manual_review)}</strong>
        </div>
      </div>

      <div className="info-card">
        <h3>RuleResultList</h3>
        <RuleResultList ruleResults={verification.rule_results} />
      </div>

      <div className="split-grid">
        <div className="info-card">
          <h3>request evidence</h3>
          <dl className="detail-kv">
            {Object.entries(verification.evidence.request).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{Array.isArray(value) ? value.join(", ") : String(value)}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="info-card">
          <h3>warnings</h3>
          <ul>
            {verification.warnings.length ? (
              verification.warnings.map((warning) => <li key={warning}>{warning}</li>)
            ) : (
              <li>无额外 warning</li>
            )}
          </ul>
        </div>
      </div>
    </section>
  );
}
