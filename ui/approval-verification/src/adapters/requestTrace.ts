export class RequestTraceError extends Error {
  requestId: string;
  cause?: unknown;

  constructor(message: string, requestId: string, options?: { cause?: unknown }) {
    super(message);
    this.name = "RequestTraceError";
    this.requestId = requestId;
    this.cause = options?.cause;
  }
}

export function getRequestIdFromError(error: unknown): string | null {
  if (error instanceof RequestTraceError) {
    return error.requestId;
  }
  return null;
}

export function resolveRequestId(input: {
  response?: { request_id?: string | null } | null;
  error?: unknown;
}): string | null {
  const responseRequestId = input.response?.request_id;
  if (responseRequestId) {
    return responseRequestId;
  }
  return getRequestIdFromError(input.error);
}
