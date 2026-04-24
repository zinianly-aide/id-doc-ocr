import type {
  ApprovalVerificationViewModel,
  DataSourceMode,
  MockScenario,
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
): Promise<RawAnalyzeResponse> {
  if (mode === "real") {
    return analyzeDocumentReal(scenario);
  }
  return analyzeDocumentMock(scenario);
}

export async function verifyAttachment(
  mode: DataSourceMode,
  scenario: MockScenario,
): Promise<RawVerifyResponse> {
  if (mode === "real") {
    return verifyAttachmentReal(scenario);
  }
  return verifyAttachmentMock(scenario);
}

export function buildPageViewModel(input: {
  rawPageModel: RawApprovalVerificationPageModel;
  rawAnalyzeResponse?: RawAnalyzeResponse;
  rawVerifyResponse?: RawVerifyResponse;
}): ApprovalVerificationViewModel {
  return buildApprovalPageModel(input);
}
