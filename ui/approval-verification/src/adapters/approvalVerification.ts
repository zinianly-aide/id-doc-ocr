import type {
  AnalysisResponse,
  ApprovalVerificationMockPage,
  DataSourceMode,
  MockScenario,
  VerificationResponse,
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

export async function getApprovalVerificationPageModel(
  mode: DataSourceMode,
  scenario: MockScenario,
): Promise<ApprovalVerificationMockPage> {
  if (mode === "real") {
    return getApprovalVerificationRealShell(scenario);
  }
  return getApprovalVerificationMock(scenario);
}

export async function analyzeDocument(
  mode: DataSourceMode,
  scenario: MockScenario,
): Promise<AnalysisResponse> {
  if (mode === "real") {
    return analyzeDocumentReal(scenario);
  }
  return analyzeDocumentMock(scenario);
}

export async function verifyAttachment(
  mode: DataSourceMode,
  scenario: MockScenario,
): Promise<VerificationResponse> {
  if (mode === "real") {
    return verifyAttachmentReal(scenario);
  }
  return verifyAttachmentMock(scenario);
}
