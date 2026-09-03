export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const RAW_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;
const API_BASE_URL = (RAW_BASE_URL && RAW_BASE_URL.trim() ? RAW_BASE_URL.trim() : "http://localhost:8000").replace(/\/+$/, "");

export const DEFAULT_READ_TIMEOUT_MS = 15_000;
export const DEFAULT_PIPELINE_TIMEOUT_MS = 180_000;

interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

function sanitizeErrorMessage(rawMessage: string | null | undefined, fallback: string): string {
  if (!rawMessage || typeof rawMessage !== "string") {
    return fallback;
  }
  const clean = rawMessage.trim();
  // If the error contains python traceback markers or internal filesystem paths, sanitize to standard fallback
  if (
    clean.includes("Traceback (most recent call last)") ||
    clean.includes("File \"") ||
    clean.includes("line ") ||
    clean.includes("internal server error")
  ) {
    return "Server encountered an issue processing the request. Please try again.";
  }
  return clean;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { timeoutMs = DEFAULT_READ_TIMEOUT_MS, ...fetchOptions } = options;
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${cleanEndpoint}`;

  const defaultHeaders: HeadersInit = {
    Accept: "application/json",
  };

  if (!(fetchOptions.body instanceof FormData)) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  const signal = timeoutMs > 0 ? AbortSignal.timeout(timeoutMs) : undefined;

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal,
      headers: {
        ...defaultHeaders,
        ...fetchOptions.headers,
      },
    });

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}`;
      try {
        const errorData = await response.json();
        if (typeof errorData?.detail === "string") {
          errorMessage = sanitizeErrorMessage(errorData.detail, errorMessage);
        } else if (typeof errorData?.error_message === "string") {
          errorMessage = sanitizeErrorMessage(errorData.error_message, errorMessage);
        } else if (typeof errorData?.message === "string") {
          errorMessage = sanitizeErrorMessage(errorData.message, errorMessage);
        }
      } catch {
        // Non-JSON response (e.g. 502/504 gateway error)
        if (response.status === 502 || response.status === 504) {
          errorMessage = "The FinDoc AI backend service is currently unreachable.";
        }
      }

      throw new ApiError(errorMessage, response.status);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  } catch (error: unknown) {
    if (error instanceof ApiError) {
      throw error;
    }

    // Handle timeout abort
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new ApiError(
        "Request timed out while waiting for the server. Please try again.",
        408
      );
    }

    // Handle offline / connection refused
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new ApiError(
        "Unable to reach the FinDoc AI server. Please verify the backend is running.",
        503
      );
    }

    throw new ApiError(
      "An unexpected error occurred while contacting the FinDoc AI server. Please try again.",
      500
    );
  }
}