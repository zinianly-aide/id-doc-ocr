import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { buildApprovalPageModel } from "../src/adapters/viewModelBuilders.ts";

function loadPageModel() {
  const fixturePath = resolve(process.cwd(), "../../examples/mock-ui/approval-verification-page.pass.json");
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
