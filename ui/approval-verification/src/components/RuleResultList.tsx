import type { RuleResult } from "@/types";

interface RuleResultListProps {
  ruleResults: RuleResult[];
}

export function RuleResultList({ ruleResults }: RuleResultListProps) {
  return (
    <div className="rule-list">
      {ruleResults.map((rule) => (
        <article
          key={rule.rule_code}
          className={`rule-card rule-card--${rule.passed ? "passed" : rule.severity}`}
        >
          <div className="rule-card__top">
            <strong>{rule.rule_code}</strong>
            <span>{rule.passed ? "passed" : "failed"}</span>
          </div>
          <div className="rule-card__meta">
            <span>severity: {rule.severity}</span>
            <span>score_delta: {rule.score_delta}</span>
          </div>
          <p>{rule.message}</p>
        </article>
      ))}
    </div>
  );
}
