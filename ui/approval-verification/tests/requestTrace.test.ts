import test from "node:test";
import assert from "node:assert/strict";
import { RequestTraceError, getRequestIdFromError } from "../src/adapters/requestTrace.ts";

test("getRequestIdFromError returns null for plain errors", () => {
  assert.equal(getRequestIdFromError(new Error("boom")), null);
});

test("getRequestIdFromError extracts request_id from RequestTraceError", () => {
  const error = new RequestTraceError("verify failed", "LV-SICK-TRACE-001");
  assert.equal(getRequestIdFromError(error), "LV-SICK-TRACE-001");
});
