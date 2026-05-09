import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { buildApprovalPageModel } from "../src/adapters/viewModelBuilders.ts";

const TEST_DIR = dirname(fileURLToPath(import.meta.url));

function loadPageModel() {
  const fixturePath = resolve(TEST_DIR, "../../../examples/mock-ui/approval-verification-page.pass.json");
  return JSON.parse(readFileSync(fixturePath, "utf-8"));
}

test("buildApprovalPageModel uses latest analyze request_id in request header when analyze response is refreshed", () => {
  const rawPageModel = loadPageModel();
  const rawAnalyzeResponse = {
    ...rawPageModel.analyzeResponse,
    request_id: "LV-SICK-ANALYZE-123",
  };

  const viewModel = buildApprovalPageModel({
    rawPageModel,
    rawAnalyzeResponse,
  });

  assert.equal(viewModel.requestHeader.requestId, "LV-SICK-ANALYZE-123");
});

test("buildApprovalPageModel uses latest verify request payload in header and attachment metadata", () => {
  const rawPageModel = loadPageModel();
  const rawVerifyResponse = {
    ...rawPageModel.verifyResponse,
    request_id: "LV-SICK-VERIFY-456",
    filename: "diagnosis_generated_001.png",
    verification: {
      ...rawPageModel.verifyResponse.verification,
      evidence: {
        ...rawPageModel.verifyResponse.verification.evidence,
        request: {
          ...rawPageModel.verifyResponse.verification.evidence.request,
          applicant_name: "张三",
          leave_type: "SICK",
          leave_start_date: "2026-03-10",
          leave_end_date: "2026-03-16",
        },
      },
    },
  };

  const viewModel = buildApprovalPageModel({
    rawPageModel,
    rawVerifyResponse,
  });

  assert.equal(viewModel.requestHeader.requestId, "LV-SICK-VERIFY-456");
  assert.equal(viewModel.requestHeader.applicantName, "张三");
  assert.equal(viewModel.requestHeader.leaveType, "SICK");
  assert.equal(viewModel.requestHeader.leaveDateRange, "2026-03-10 ~ 2026-03-16");
  assert.equal(viewModel.attachments[0]?.filename, "diagnosis_generated_001.png");
});

test("buildApprovalPageModel derives quality review reason when review has no warnings but still needs manual review", () => {
  const rawPageModel = loadPageModel();
  const rawVerifyResponse = {
    ...rawPageModel.verifyResponse,
    verification: {
      ...rawPageModel.verifyResponse.verification,
      verify_status: "REVIEW",
      warnings: [],
      needs_manual_review: true,
      rule_results: rawPageModel.verifyResponse.verification.rule_results.map((rule: { passed: boolean }) => ({
        ...rule,
        passed: true,
      })),
    },
  };

  const viewModel = buildApprovalPageModel({
    rawPageModel,
    rawVerifyResponse,
  });

  assert.equal(
    viewModel.verification.reviewReasonHint,
    "业务字段已基本匹配，但材料质量门控/识别置信度仍未达到自动通过标准，建议人工复核。",
  );
});

test("buildApprovalPageModel fails closed with clear message for partial verify response", () => {
  const rawPageModel = loadPageModel();
  const rawVerifyResponse = {
    request_id: "LV-SICK-PARTIAL-789",
    verification: rawPageModel.verifyResponse.verification,
  };

  assert.throws(
    () => buildApprovalPageModel({
      rawPageModel,
      rawVerifyResponse: rawVerifyResponse as never,
    }),
    /verify response is missing analysis payload/i,
  );
});
