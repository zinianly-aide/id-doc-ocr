import test from "node:test";
import assert from "node:assert/strict";
import {
  buildVerificationRunMeta,
  formatVerificationTimestamp,
} from "../src/components/verificationRunState.ts";

test("buildVerificationRunMeta uses the latest verify completion time for status summary and timeline", () => {
  const startedAt = new Date("2026-04-29T13:20:00.000Z");
  const completedAt = new Date("2026-04-29T13:20:05.000Z");

  const meta = buildVerificationRunMeta({
    verifyStatus: "success",
    latestStartedAt: startedAt,
    latestCompletedAt: completedAt,
  });

  assert.equal(meta.statusText, "已完成当前核验");
  assert.equal(meta.completedAtLabel, formatVerificationTimestamp(completedAt));
  assert.deepEqual(meta.timelineItems.map((item) => item.label), ["文档上传", "文档分析", "规则验证", "完成核验"]);
  assert.equal(meta.timelineItems.at(-1)?.time, formatVerificationTimestamp(completedAt, { timeOnly: true }));
});

test("buildVerificationRunMeta shows loading state before verify completes", () => {
  const startedAt = new Date("2026-04-29T13:20:00.000Z");

  const meta = buildVerificationRunMeta({
    verifyStatus: "loading",
    latestStartedAt: startedAt,
    latestCompletedAt: null,
  });

  assert.equal(meta.statusText, "系统正在核验");
  assert.equal(meta.completedAtLabel, "核验进行中");
  assert.equal(meta.timelineItems.at(-1)?.label, "完成核验");
  assert.equal(meta.timelineItems.at(-1)?.time, "进行中");
});
