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

test("buildApprovalPageModel uses latest verify request_id in request header when verify response is refreshed", () => {
  const rawPageModel = loadPageModel();
  const rawVerifyResponse = {
    ...rawPageModel.verifyResponse,
    request_id: "LV-SICK-VERIFY-456",
  };

  const viewModel = buildApprovalPageModel({
    rawPageModel,
    rawVerifyResponse,
  });

  assert.equal(viewModel.requestHeader.requestId, "LV-SICK-VERIFY-456");
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
