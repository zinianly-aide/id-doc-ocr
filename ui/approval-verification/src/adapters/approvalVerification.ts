import type {
  ApprovalVerificationViewModel,
  DataSourceMode,
  MockScenario,
  OpenAIVerificationResponse,
  RawAnalyzeResponse,
  RawApprovalVerificationPageModel,
  RawVerifyResponse,
} from "@/types";
import {
  analyzeDocumentMock,
  getApprovalVerificationMock,
  verifyAttachmentMock,
} from "./mockApprovalVerification";
import {
  analyzeDocumentReal,
  getApprovalVerificationRealShell,
  verifyAttachmentReal,
  verifyAttachmentWithOpenAIReal,
} from "./realApprovalVerification";
import { buildApprovalPageModel } from "./viewModelBuilders";

export async function getApprovalVerificationPageModel(
  mode: DataSourceMode,
  scenario: MockScenario,
): Promise<RawApprovalVerificationPageModel> {
  if (mode === "real") {
    return getApprovalVerificationRealShell(scenario);
  }
  return getApprovalVerificationMock(scenario);
}

export async function analyzeDocument(
  mode: DataSourceMode,
  scenario: MockScenario,
  selectedFile: File | null = null,
): Promise<RawAnalyzeResponse> {
  if (mode === "real") {
    return analyzeDocumentReal(scenario, selectedFile);
  }
  return analyzeDocumentMock(scenario);
}

export async function verifyAttachment(
  mode: DataSourceMode,
  scenario: MockScenario,
  selectedFile: File | null = null,
): Promise<RawVerifyResponse> {
  if (mode === "real") {
    return verifyAttachmentReal(scenario, selectedFile);
  }
  return verifyAttachmentMock(scenario);
}

export async function verifyAttachmentWithOpenAI(
  mode: DataSourceMode,
  scenario: MockScenario,
  selectedFile: File | null = null,
): Promise<OpenAIVerificationResponse> {
  if (mode !== "real") {
    throw new Error("OpenAI 校验仅支持 real adapter mode。");
  }
  return verifyAttachmentWithOpenAIReal(scenario, selectedFile);
}

export function buildPageViewModel(input: {
  rawPageModel: RawApprovalVerificationPageModel;
  rawAnalyzeResponse?: RawAnalyzeResponse;
  rawVerifyResponse?: RawVerifyResponse;
}): ApprovalVerificationViewModel {
  return buildApprovalPageModel(input);
}
