import type {
  DifyChatResponse,
  LeaveAuditDetailResponse,
  LeaveAuditResultResponse,
  LeaveAuditReviewResponse,
  LeaveAuditStatsResponse,
  LeaveAuditSyncResponse,
  LeaveAuditTaskListResponse,
  LeaveAuditConfigResponse,
  FieldMappingItem,
  PromptConfigItem,
  RuleConfigItem,
  OcrResponse,
} from "@/types/leaveAudit";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = payload?.detail ?? response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload as T;
}

async function requestFormJson<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = payload?.detail ?? response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload as T;
}

export const leaveAuditApi = {
  listTasks: (params?: { status?: string }): Promise<LeaveAuditTaskListResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.status) {
      searchParams.set("status", params.status);
    }
    const query = searchParams.toString();
    return requestJson<LeaveAuditTaskListResponse>(`/leave-audit/tasks${query ? `?${query}` : ""}`);
  },

  getTask: (requestId: string): Promise<LeaveAuditDetailResponse> =>
    requestJson<LeaveAuditDetailResponse>(`/leave-audit/tasks/${encodeURIComponent(requestId)}`),

  syncTasks: (): Promise<LeaveAuditSyncResponse> =>
    requestJson<LeaveAuditSyncResponse>("/leave-audit/sync", { method: "POST" }),

  runTask: (requestId: string, fieldParserBackend?: "plugin" | "dify"): Promise<LeaveAuditResultResponse> => {
    const searchParams = new URLSearchParams();
    if (fieldParserBackend) {
      searchParams.set("field_parser_backend", fieldParserBackend);
    }
    const query = searchParams.toString();
    return requestJson<LeaveAuditResultResponse>(
      `/leave-audit/tasks/${encodeURIComponent(requestId)}/run${query ? `?${query}` : ""}`,
      { method: "POST" },
    );
  },

  submitReview: (
    requestId: string,
    body: { decision: string; reviewer: string; comment?: string },
  ): Promise<LeaveAuditReviewResponse> =>
    requestJson<LeaveAuditReviewResponse>(`/leave-audit/tasks/${encodeURIComponent(requestId)}/review`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  callbackTask: (requestId: string): Promise<LeaveAuditResultResponse> =>
    requestJson<LeaveAuditResultResponse>(`/leave-audit/tasks/${encodeURIComponent(requestId)}/callback`, { method: "POST" }),

  stats: (): Promise<LeaveAuditStatsResponse> => requestJson<LeaveAuditStatsResponse>("/leave-audit/stats"),

  getConfig: (): Promise<LeaveAuditConfigResponse> => requestJson<LeaveAuditConfigResponse>("/leave-audit/config"),

  updateFieldMappings: (mappings: FieldMappingItem[]): Promise<{ field_mappings: FieldMappingItem[] }> =>
    requestJson<{ field_mappings: FieldMappingItem[] }>("/leave-audit/config/field-mappings", {
      method: "PUT",
      body: JSON.stringify({ mappings }),
    }),

  updateRuleConfigs: (configs: RuleConfigItem[]): Promise<{ rule_configs: RuleConfigItem[] }> =>
    requestJson<{ rule_configs: RuleConfigItem[] }>("/leave-audit/config/rules", {
      method: "PUT",
      body: JSON.stringify({ configs }),
    }),

  updatePromptConfigs: (configs: PromptConfigItem[]): Promise<{ prompt_configs: PromptConfigItem[] }> =>
    requestJson<{ prompt_configs: PromptConfigItem[] }>("/leave-audit/config/prompts", {
      method: "PUT",
      body: JSON.stringify({ configs }),
    }),

  runOcr: (file: File, ocrBackend = "rapidocr"): Promise<OcrResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    if (ocrBackend) {
      formData.append("ocr_backend", ocrBackend);
    }
    return requestFormJson<OcrResponse>("/ocr", formData);
  },

  askDify: (body: { question: string; ocr_text?: string; conversation_id?: string | null }): Promise<DifyChatResponse> =>
    requestJson<DifyChatResponse>("/dify-chat", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
