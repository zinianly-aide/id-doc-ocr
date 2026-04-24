import passPage from "../../../../examples/mock-ui/approval-verification-page.pass.json";
import reviewPage from "../../../../examples/mock-ui/approval-verification-page.review.json";
import type {
  RawAnalyzeResponse,
  RawApprovalVerificationPageModel,
  MockScenario,
  RawVerifyResponse,
} from "@/types";

const scenarioMap: Record<MockScenario, RawApprovalVerificationPageModel> = {
  pass: passPage as RawApprovalVerificationPageModel,
  review: reviewPage as RawApprovalVerificationPageModel,
};

function clone<T>(value: T): T {
  return structuredClone(value);
}

function delay(ms = 180): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function getScenarioRawPageModel(scenario: MockScenario): RawApprovalVerificationPageModel {
  return clone(scenarioMap[scenario]);
}

export async function getApprovalVerificationMock(
  scenario: MockScenario = "pass",
): Promise<RawApprovalVerificationPageModel> {
  await delay();
  return getScenarioRawPageModel(scenario);
}

export async function analyzeDocumentMock(
  scenario: MockScenario = "pass",
): Promise<RawAnalyzeResponse> {
  await delay();
  return clone(scenarioMap[scenario].analyzeResponse);
}

export async function verifyAttachmentMock(
  scenario: MockScenario = "pass",
): Promise<RawVerifyResponse> {
  await delay();
  return clone(scenarioMap[scenario].verifyResponse);
}
