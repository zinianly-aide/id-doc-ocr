import type { AsyncStatus, VerificationViewModel } from "@/types";
import { RiskBadge } from "./RiskBadge";
import { RuleResultList } from "./RuleResultList";

interface VerificationPanelProps {
  verification: VerificationViewModel | null;
  verifyStatus: AsyncStatus;
  errorMessage?: string | null;
  inconsistencyMessage?: string | null;
}

export function VerificationPanel({ verification, verifyStatus, errorMessage, inconsistencyMessage }: VerificationPanelProps) {
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

      {verifyStatus === "error" ? (
        <div className="panel-alert panel-alert--error">
          <strong>Verification request failed.</strong>
          <p>{errorMessage ?? "verify 调用失败。"}</p>
          <p>当前显示的是上一次结果。</p>
        </div>
      ) : null}

      {inconsistencyMessage ? (
        <div className="panel-alert panel-alert--warning">
          <strong>Analysis / verification mismatch</strong>
          <p>{inconsistencyMessage}</p>
        </div>
      ) : null}

      <div className="info-card info-card--emphasis">
        <div className="section-heading-row">
          <h3>Verification decision</h3>
          <div className="status-stack">
            <RiskBadge label={verification.verifyStatus} tone={verification.verifyStatus} />
            <RiskBadge label={verification.riskLevel} tone={verification.riskLevel} />
          </div>
        </div>
        <p className="muted">这是业务规则核验结论；当与左侧分析建议不一致时，请以业务核验结论为主，并结合分析风险人工复核。</p>
        <div className="summary-grid">
          <div className="summary-tile">
            <span className="summary-tile__label">verification.verify_status</span>
            <strong>{verification.verifyStatus}</strong>
          </div>
          <div className="summary-tile">
            <span className="summary-tile__label">verification.risk_level</span>
            <strong>{verification.riskLevel}</strong>
          </div>
          <div className="summary-tile">
            <span className="summary-tile__label">verification.risk_score</span>
            <strong>{verification.riskScore}</strong>
          </div>
          <div className="summary-tile">
            <span className="summary-tile__label">needs_manual_review</span>
            <strong>{String(verification.needsManualReview)}</strong>
          </div>
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
