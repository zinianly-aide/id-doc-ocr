import type { VerifyStatus } from "@/types";

export interface PilotDecisionUiState {
  suggestionTone: "pass" | "review" | "reject";
  decisionAdvice: string;
  decisionSubtitle: string;
  staleResultWarning: string | null;
}

function getStatusTone(status: VerifyStatus): "pass" | "review" | "reject" {
  if (status === "PASS") return "pass";
  if (status === "REJECT") return "reject";
  return "review";
}

function getDecisionAdvice(status: VerifyStatus): string {
  if (status === "PASS") return "建议通过";
  if (status === "REJECT") return "建议驳回";
  return "建议人工复核";
}

function getDecisionSubtitle(status: VerifyStatus): string {
  if (status === "PASS") return "材料满足当前审批要求，可直接完成审批。";
  if (status === "REJECT") return "材料存在关键问题，建议驳回或退回补正。";
  return "材料存在待确认风险，建议先转人工复核。";
}

export function derivePilotDecisionUiState(input: {
  verifyStatus: VerifyStatus;
  verifyError: string | null;
}): PilotDecisionUiState {
  if (input.verifyError) {
    return {
      suggestionTone: "review",
      decisionAdvice: "建议人工处理",
      decisionSubtitle: "本次核验失败，请转人工处理；当前页面仍展示上一次结果，仅供参考。",
      staleResultWarning: "当前展示的是上一次核验结果，请勿直接据此完成审批。",
    };
  }

  return {
    suggestionTone: getStatusTone(input.verifyStatus),
    decisionAdvice: getDecisionAdvice(input.verifyStatus),
    decisionSubtitle: getDecisionSubtitle(input.verifyStatus),
    staleResultWarning: null,
  };
}
