import test from "node:test";
import assert from "node:assert/strict";
import { derivePilotDecisionUiState } from "../src/components/pilotDecisionState.ts";

test("derivePilotDecisionUiState keeps PASS approval summary when verify succeeds", () => {
  const state = derivePilotDecisionUiState({
    verifyStatus: "PASS",
    verifyError: null,
  });

  assert.deepEqual(state, {
    suggestionTone: "pass",
    decisionAdvice: "建议通过",
    decisionSubtitle: "材料满足当前审批要求，可直接完成审批。",
    staleResultWarning: null,
  });
});

test("derivePilotDecisionUiState routes to manual handling when verify fails and stale result is shown", () => {
  const state = derivePilotDecisionUiState({
    verifyStatus: "PASS",
    verifyError: "verify failed",
  });

  assert.deepEqual(state, {
    suggestionTone: "review",
    decisionAdvice: "建议人工处理",
    decisionSubtitle: "本次核验失败，请转人工处理；当前页面仍展示上一次结果，仅供参考。",
    staleResultWarning: "当前展示的是上一次核验结果，请勿直接据此完成审批。",
  });
});
