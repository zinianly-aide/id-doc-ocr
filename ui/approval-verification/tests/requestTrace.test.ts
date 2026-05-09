import test from "node:test";
import assert from "node:assert/strict";
import { RequestTraceError, getRequestIdFromError, resolveRequestId } from "../src/adapters/requestTrace.ts";

test("getRequestIdFromError returns null for plain errors", () => {
  assert.equal(getRequestIdFromError(new Error("boom")), null);
});

test("getRequestIdFromError extracts request_id from RequestTraceError", () => {
  const error = new RequestTraceError("verify failed", "LV-SICK-TRACE-001");
  assert.equal(getRequestIdFromError(error), "LV-SICK-TRACE-001");
});

test("resolveRequestId prefers response request_id for partial verify payload failures", () => {
  const error = new Error("verify response is missing analysis payload");
  const response = {
    request_id: "LV-SICK-PARTIAL-789",
    verification: {},
  };

  assert.equal(resolveRequestId({ response, error }), "LV-SICK-PARTIAL-789");
});

test("resolveRequestId falls back to traced request_id when response has no request_id", () => {
  const error = new RequestTraceError("verify failed", "LV-SICK-TRACE-002");

  assert.equal(resolveRequestId({ response: null, error }), "LV-SICK-TRACE-002");
});
