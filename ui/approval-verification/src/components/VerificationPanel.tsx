import type { VerificationViewModel } from "@/types";
import { RiskBadge } from "./RiskBadge";
import { RuleResultList } from "./RuleResultList";

interface VerificationPanelProps {
  verification: VerificationViewModel | null;
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
          <p>组件层只消费 ViewModel，不直接读取 raw verify response。</p>
        </div>
        <div className="status-stack">
          <RiskBadge label={verification.verifyStatus} tone={verification.verifyStatus} />
          <RiskBadge label={verification.riskLevel} tone={verification.riskLevel} />
        </div>
      </div>

      <div className="summary-grid">
        <div className="summary-tile">
          <span className="summary-tile__label">summary_message</span>
          <strong>{verification.summaryMessage}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">matched_attachment_type</span>
          <strong>{verification.matchedAttachmentType}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">risk_score</span>
          <strong>{verification.riskScore}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">needs_manual_review</span>
          <strong>{String(verification.needsManualReview)}</strong>
        </div>
      </div>

      <div className="info-card">
        <h3>RuleResultList</h3>
        <RuleResultList ruleResults={verification.ruleResults} />
      </div>

      <div className="split-grid">
        <div className="info-card">
          <h3>request evidence</h3>
          <dl className="detail-kv">
            {verification.requestEvidence.map((entry) => (
              <div key={entry.key}>
                <dt>{entry.label}</dt>
                <dd>{entry.value}</dd>
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
