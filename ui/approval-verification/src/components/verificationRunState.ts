import type { AsyncStatus } from "../types.ts";

export interface VerificationTimelineItem {
  label: string;
  time: string;
  tone: "pass" | "review" | "info";
}

export interface VerificationRunMeta {
  statusText: string;
  completedAtLabel: string;
  timelineItems: VerificationTimelineItem[];
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatVerificationTimestamp(
  date: Date,
  options?: { timeOnly?: boolean },
): string {
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  const seconds = pad(date.getSeconds());

  if (options?.timeOnly) {
    return `${hours}:${minutes}:${seconds}`;
  }

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

function offsetTime(base: Date, offsetSeconds: number): Date {
  return new Date(base.getTime() + offsetSeconds * 1000);
}

export function buildVerificationRunMeta(input: {
  verifyStatus: AsyncStatus;
  latestStartedAt: Date | null;
  latestCompletedAt: Date | null;
}): VerificationRunMeta {
  const startedAt = input.latestStartedAt;
  const completedAt = input.latestCompletedAt;
  const statusText = input.verifyStatus === "loading" ? "系统正在核验" : "已完成当前核验";
  const completedAtLabel = completedAt
    ? formatVerificationTimestamp(completedAt)
    : input.verifyStatus === "loading"
      ? "核验进行中"
      : "待开始";

  if (!startedAt) {
    return {
      statusText,
      completedAtLabel,
      timelineItems: [
        { label: "文档上传", time: "待开始", tone: "info" },
        { label: "文档分析", time: "待开始", tone: "info" },
        { label: "规则验证", time: "待开始", tone: "info" },
        { label: "完成核验", time: input.verifyStatus === "loading" ? "进行中" : completedAtLabel, tone: "info" },
      ],
    };
  }

  return {
    statusText,
    completedAtLabel,
    timelineItems: [
      { label: "文档上传", time: formatVerificationTimestamp(startedAt, { timeOnly: true }), tone: "pass" },
      { label: "文档分析", time: formatVerificationTimestamp(offsetTime(startedAt, 1), { timeOnly: true }), tone: "pass" },
      { label: "规则验证", time: formatVerificationTimestamp(offsetTime(startedAt, 2), { timeOnly: true }), tone: "pass" },
      {
        label: "完成核验",
        time: completedAt ? formatVerificationTimestamp(completedAt, { timeOnly: true }) : "进行中",
        tone: completedAt ? "info" : "review",
      },
    ],
  };
}
