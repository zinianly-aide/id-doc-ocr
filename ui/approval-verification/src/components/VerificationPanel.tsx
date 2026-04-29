import type { AsyncStatus, VerificationViewModel } from "@/types";
import { RiskBadge } from "./RiskBadge";
import { RuleResultList } from "./RuleResultList";

interface VerificationPanelProps {
  verification: VerificationViewModel | null;
  verifyStatus: AsyncStatus;
  errorMessage?: string | null;
  inconsistencyMessage?: string | null;
}

function getDecisionSummary(verification: VerificationViewModel): string {
  if (verification.verifyStatus === "PASS") {
    return "业务规则核验通过，可作为审批结论基线。";
  }
  if (verification.verifyStatus === "REJECT") {
    return "业务规则核验未通过，应按拒绝/驳回方向处理。";
  }
  return "业务规则未能直接放行，当前应进入人工复核。";
}

function getManualReviewHint(verification: VerificationViewModel): string {
  if (!verification.needsManualReview) {
    return "当前无需人工复核，可直接参考业务核验结论。";
  }
  if (verification.warnings.length > 0) {
    return `建议人工复核，重点关注：${verification.warnings.join("；")}`;
  }
  return "建议人工复核，但当前未返回额外 warning，请结合规则结果查看。";
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

  const showInconsistency = Boolean(inconsistencyMessage) && verifyStatus !== "error";

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
          <strong>本次业务核验调用失败</strong>
          <p>{errorMessage ?? "verify 调用失败。"}</p>
          <p>当前仍展示上一次核验结果，仅供参考，请勿直接据此完成审批。</p>
        </div>
      ) : null}

      {showInconsistency ? (
        <div className="panel-alert panel-alert--warning">
          <strong>分析建议与业务核验结论不一致</strong>
          <p>{inconsistencyMessage}</p>
          <p>处理原则：右侧业务核验结论优先，左侧 analysis 风险作为补充判断依据。</p>
        </div>
      ) : null}

      <div className="info-card info-card--emphasis">
        <div className="section-heading-row">
          <h3>业务核验结论</h3>
          <div className="status-stack">
            <RiskBadge label={verification.verifyStatus} tone={verification.verifyStatus} />
            <RiskBadge label={verification.riskLevel} tone={verification.riskLevel} />
          </div>
        </div>
        <p className="muted">{getDecisionSummary(verification)}</p>
        {verifyStatus === "error" ? <p className="muted">注意：当前卡片内容来自旧结果，不是本次最新 verify 返回。</p> : null}
        <div className="summary-grid">
          <div className="summary-tile">
            <span className="summary-tile__label">核验状态</span>
            <strong>{verification.verifyStatus}</strong>
          </div>
          <div className="summary-tile">
            <span className="summary-tile__label">风险等级</span>
            <strong>{verification.riskLevel}</strong>
          </div>
          <div className="summary-tile">
            <span className="summary-tile__label">风险分</span>
            <strong>{verification.riskScore}</strong>
          </div>
          <div className="summary-tile">
            <span className="summary-tile__label">人工复核</span>
            <strong>{verification.needsManualReview ? "需要" : "无需"}</strong>
          </div>
        </div>
      </div>

      <div className="summary-grid">
        <div className="summary-tile">
          <span className="summary-tile__label">结论摘要</span>
          <strong>{verification.summaryMessage}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">匹配材料类型</span>
          <strong>{verification.matchedAttachmentType}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">规则命中数</span>
          <strong>{verification.ruleResults.length}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">预警数</span>
          <strong>{verification.warnings.length}</strong>
        </div>
      </div>

      <div className="info-card">
        <h3>人工复核提示</h3>
        <p>{getManualReviewHint(verification)}</p>
      </div>

      <div className="info-card">
        <h3>规则核验明细</h3>
        <RuleResultList ruleResults={verification.ruleResults} />
      </div>

      <div className="split-grid">
        <div className="info-card">
          <h3>请求侧证据</h3>
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
          <h3>风险 / warning</h3>
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
