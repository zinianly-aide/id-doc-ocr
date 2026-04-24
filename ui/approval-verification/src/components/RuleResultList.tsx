import type { RuleResultViewModel } from "@/types";

interface RuleResultListProps {
  ruleResults: RuleResultViewModel[];
}

export function RuleResultList({ ruleResults }: RuleResultListProps) {
  return (
    <div className="rule-list">
      {ruleResults.map((rule) => (
        <article
          key={rule.ruleCode}
          className={`rule-card rule-card--${rule.passed ? "passed" : rule.severity}`}
        >
          <div className="rule-card__top">
            <strong>{rule.ruleCode}</strong>
            <span>{rule.passed ? "passed" : "failed"}</span>
          </div>
          <div className="rule-card__meta">
            <span>severity: {rule.severity}</span>
            <span>score_delta: {rule.scoreDelta}</span>
          </div>
          <p>{rule.message}</p>
        </article>
      ))}
    </div>
  );
}
