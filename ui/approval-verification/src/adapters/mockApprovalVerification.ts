import passPage from "../../../../examples/mock-ui/approval-verification-page.pass.json";
import reviewPage from "../../../../examples/mock-ui/approval-verification-page.review.json";
import type {
  RawAnalyzeResponse,
  RawApprovalVerificationPageModel,
  MockScenario,
  RawVerifyResponse,
} from "@/types";

type ScenarioPageJson = Omit<RawApprovalVerificationPageModel, "analyzeResponse" | "verifyResponse"> & {
  analyzeResponse: Omit<RawAnalyzeResponse, "request_id"> & { request_id?: string };
  verifyResponse: Omit<RawVerifyResponse, "request_id"> & { request_id?: string };
};

function normalizeScenarioPage(page: ScenarioPageJson): RawApprovalVerificationPageModel {
  const requestId = page.requestHeader.requestId;
  return {
    ...page,
    analyzeResponse: {
      ...page.analyzeResponse,
      request_id: page.analyzeResponse.request_id ?? requestId,
    },
    verifyResponse: {
      ...page.verifyResponse,
      request_id: page.verifyResponse.request_id ?? requestId,
    },
  };
}

const scenarioMap: Record<MockScenario, RawApprovalVerificationPageModel> = {
  pass: normalizeScenarioPage(passPage as ScenarioPageJson),
  review: normalizeScenarioPage(reviewPage as ScenarioPageJson),
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
