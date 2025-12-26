export type ApiOptions = RequestInit & { token?: string };

const defaultBase = "http://localhost:8000/api";

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || defaultBase;
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  const token = options.token || getToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `API error ${response.status}`);
  }

  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.text()) as T;
}

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem("authToken");
}

export function setToken(token: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem("authToken", token);
}
