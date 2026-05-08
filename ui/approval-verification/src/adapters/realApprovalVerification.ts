import type {
  RawAnalyzeResponse,
  MockScenario,
  RawVerifyResponse,
} from "@/types";
import {
  buildAnalyzeDemoFormData,
  buildAnalyzeSelectedFileFormData,
  buildVerifyDemoFormData,
  buildVerifySelectedFileFormData,
} from "./demoRequestBuilders";
import { getScenarioRawPageModel } from "./mockApprovalVerification";
import { RequestTraceError } from "./requestTrace";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
let currentRealRequestId: string | null = null;

function buildRequestId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `LV-SICK-${crypto.randomUUID()}`;
  }
  return `LV-SICK-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
}

function nextAnalyzeRequestId(): string {
  currentRealRequestId = buildRequestId();
  return currentRealRequestId;
}

function currentVerifyRequestId(): string {
  currentRealRequestId = currentRealRequestId ?? buildRequestId();
  return currentRealRequestId;
}

async function requestJson<T>(path: string, init: RequestInit, requestId: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (error) {
    const message = error instanceof Error ? error.message : `API ${path} failed`;
    throw new RequestTraceError(message, requestId, { cause: error });
  }

  if (!response.ok) {
    const text = await response.text();
    throw new RequestTraceError(`API ${path} failed (${response.status}): ${text || response.statusText}`, requestId);
  }
  return (await response.json()) as T;
}

export async function analyzeDocumentReal(
  scenario: MockScenario = "pass",
  selectedFile: File | null = null,
): Promise<RawAnalyzeResponse> {
  const requestId = nextAnalyzeRequestId();
  const formData = selectedFile
    ? buildAnalyzeSelectedFileFormData(scenario, selectedFile)
    : await buildAnalyzeDemoFormData(scenario);
  formData.set("request_id", requestId);
  return requestJson<RawAnalyzeResponse>("/analyze-document", {
    method: "POST",
    body: formData,
  }, requestId);
}

export async function verifyAttachmentReal(
  scenario: MockScenario = "pass",
  selectedFile: File | null = null,
): Promise<RawVerifyResponse> {
  const requestId = currentVerifyRequestId();
  const formData = selectedFile
    ? buildVerifySelectedFileFormData(scenario, selectedFile)
    : await buildVerifyDemoFormData(scenario);
  formData.set("request_id", requestId);
  return requestJson<RawVerifyResponse>("/verify-attachment", {
    method: "POST",
    body: formData,
  }, requestId);
}

export async function getApprovalVerificationRealShell(scenario: MockScenario) {
  return getScenarioRawPageModel(scenario);
}
