export type ApiError = { detail?: string } | { message?: string } | unknown;

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function getToken() {
  return localStorage.getItem("mw_token");
}

export async function apiFetch<T>(
  path: string,
  opts: RequestInit & { auth?: boolean } = { auth: true },
): Promise<T> {
  const headers = new Headers(opts.headers || {});
  headers.set("Accept", "application/json");

  const needsAuth = opts.auth !== false;
  if (needsAuth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...opts, headers });
  const contentType = res.headers.get("content-type") || "";

  if (!res.ok) {
    let body: any = null;
    try {
      body = contentType.includes("application/json") ? await res.json() : await res.text();
    } catch {
      body = null;
    }
    const detail = (body && (body.detail || body.message)) || res.statusText;
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }

  if (contentType.includes("application/json")) {
    return (await res.json()) as T;
  }
  return (await res.text()) as unknown as T;
}

