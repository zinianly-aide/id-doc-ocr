import type { RiskLevel, VerifyStatus } from "@/types";

type BadgeTone = RiskLevel | VerifyStatus | "INFO";

interface RiskBadgeProps {
  label: string;
  tone: BadgeTone;
}

export function RiskBadge({ label, tone }: RiskBadgeProps) {
  return <span className={`badge badge--${tone.toLowerCase()}`}>{label}</span>;
}
