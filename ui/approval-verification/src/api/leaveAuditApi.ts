import type {
  LeaveAuditDetailResponse,
  LeaveAuditResultResponse,
  LeaveAuditReviewResponse,
  LeaveAuditStatsResponse,
  LeaveAuditSyncResponse,
  LeaveAuditTaskListResponse,
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

  runTask: (requestId: string): Promise<LeaveAuditResultResponse> =>
    requestJson<LeaveAuditResultResponse>(`/leave-audit/tasks/${encodeURIComponent(requestId)}/run`, { method: "POST" }),

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
};
