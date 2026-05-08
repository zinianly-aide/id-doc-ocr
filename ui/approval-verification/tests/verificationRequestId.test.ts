import test from "node:test";
import assert from "node:assert/strict";
import { buildRequestIdGenerator } from "../src/adapters/verificationRequestId.ts";

test("buildRequestIdGenerator generates a fresh request_id for each verify invocation", () => {
  let index = 0;
  const nextRequestId = buildRequestIdGenerator(() => `uuid-${++index}`);

  const firstVerifyRequestId = nextRequestId("verify");
  const secondVerifyRequestId = nextRequestId("verify");

  assert.equal(firstVerifyRequestId, "LV-SICK-uuid-1");
  assert.equal(secondVerifyRequestId, "LV-SICK-uuid-2");
  assert.notEqual(firstVerifyRequestId, secondVerifyRequestId);
});

test("buildRequestIdGenerator resets verify correlation after analyze starts a new run", () => {
  let index = 0;
  const nextRequestId = buildRequestIdGenerator(() => `uuid-${++index}`);

  const analyzeRequestId = nextRequestId("analyze");
  const verifyRequestId = nextRequestId("verify");

  assert.equal(analyzeRequestId, "LV-SICK-uuid-1");
  assert.equal(verifyRequestId, "LV-SICK-uuid-2");
});
