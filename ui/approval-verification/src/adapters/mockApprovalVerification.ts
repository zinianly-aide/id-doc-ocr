import passPage from "../../../../examples/mock-ui/approval-verification-page.pass.json";
import reviewPage from "../../../../examples/mock-ui/approval-verification-page.review.json";
import type {
  AnalysisResponse,
  ApprovalVerificationMockPage,
  MockScenario,
  VerificationResponse,
} from "@/types";

const scenarioMap: Record<MockScenario, ApprovalVerificationMockPage> = {
  pass: passPage as ApprovalVerificationMockPage,
  review: reviewPage as ApprovalVerificationMockPage,
};

function clone<T>(value: T): T {
  return structuredClone(value);
}

function delay(ms = 180): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function getScenarioPageModel(scenario: MockScenario): ApprovalVerificationMockPage {
  return clone(scenarioMap[scenario]);
}

export async function getApprovalVerificationMock(
  scenario: MockScenario = "pass",
): Promise<ApprovalVerificationMockPage> {
  await delay();
  return getScenarioPageModel(scenario);
}

export async function analyzeDocumentMock(
  scenario: MockScenario = "pass",
): Promise<AnalysisResponse> {
  await delay();
  return clone(scenarioMap[scenario].analyzeResponse);
}

export async function verifyAttachmentMock(
  scenario: MockScenario = "pass",
): Promise<VerificationResponse> {
  await delay();
  return clone(scenarioMap[scenario].verifyResponse);
}
