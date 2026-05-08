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
