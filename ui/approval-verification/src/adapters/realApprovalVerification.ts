import type {
  RawAnalyzeResponse,
  MockScenario,
  RawVerifyResponse,
} from "@/types";
import { buildAnalyzeDemoFormData, buildVerifyDemoFormData } from "./demoRequestBuilders";
import { getScenarioRawPageModel } from "./mockApprovalVerification";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${path} failed (${response.status}): ${text || response.statusText}`);
  }
  return (await response.json()) as T;
}

export async function analyzeDocumentReal(
  scenario: MockScenario = "pass",
): Promise<RawAnalyzeResponse> {
  const formData = await buildAnalyzeDemoFormData(scenario);
  return requestJson<RawAnalyzeResponse>("/analyze-document", {
    method: "POST",
    body: formData,
  });
}

export async function verifyAttachmentReal(
  scenario: MockScenario = "pass",
): Promise<RawVerifyResponse> {
  const formData = await buildVerifyDemoFormData(scenario);
  return requestJson<RawVerifyResponse>("/verify-attachment", {
    method: "POST",
    body: formData,
  });
}

export async function getApprovalVerificationRealShell(scenario: MockScenario) {
  return getScenarioRawPageModel(scenario);
}
