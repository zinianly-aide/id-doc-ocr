export type RequestIdStage = "analyze" | "verify" | "openai";

function defaultUuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
}

export function buildRequestIdGenerator(uuidFactory: () => string = defaultUuid) {
  return (_stage: RequestIdStage): string => `LV-SICK-${uuidFactory()}`;
}

export const nextRealRequestId = buildRequestIdGenerator();
