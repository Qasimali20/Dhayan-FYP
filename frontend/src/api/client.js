const RAW_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
const API_BASE = RAW_BASE.replace(/\/+$/, ""); // remove trailing slash

// ---- Token storage ----
export function getToken() {
  return localStorage.getItem("dhyan_jwt") || "";
}

export function setToken(access) {
  localStorage.setItem("dhyan_jwt", access);
}

export function getRefreshToken() {
  return localStorage.getItem("dhyan_refresh") || "";
}

export function setRefreshToken(refresh) {
  localStorage.setItem("dhyan_refresh", refresh);
}

export function clearToken() {
  localStorage.removeItem("dhyan_jwt");
  localStorage.removeItem("dhyan_refresh");
}

// ---- Internal helpers ----
function joinUrl(base, path) {
  if (!path) return base;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  if (!path.startsWith("/")) path = "/" + path;
  return `${base}${path}`;
}

async function safeJson(res) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

function buildError(res, data) {
  const detail =
    (data && (data.detail || data.message)) ||
    (typeof data === "string" ? data : null) ||
    `HTTP ${res.status}`;

  const err = new Error(detail);
  err.status = res.status;
  err.payload = data;
  return err;
}

// ---- Refresh logic ----
let refreshPromise = null;

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) throw new Error("Session expired. Please login again.");

  // Ensure only one refresh in flight
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const res = await fetch(joinUrl(API_BASE, "/api/v1/auth/refresh"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      });

      const data = await safeJson(res);

      if (!res.ok) {
        clearToken();
        throw buildError(res, data);
      }

      // SimpleJWT returns { access } for refresh endpoint
      if (data?.access) setToken(data.access);
      else throw new Error("Refresh failed: missing access token");

      return data.access;
    })().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}

// ---- Main fetch ----
export async function apiFetch(
  path,
  { method = "GET", body, rawBody, auth = true, retryOnAuth = true, headers: customHeaders } = {}
) {
  const headers = customHeaders ?? { "Content-Type": "application/json" };

  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }

  // If rawBody (e.g. FormData), use it directly; otherwise JSON-encode body
  let fetchBody;
  if (rawBody) {
    fetchBody = rawBody;
    // Let browser set Content-Type (with boundary for multipart)
    delete headers["Content-Type"];
  } else if (body) {
    fetchBody = JSON.stringify(body);
  }

  const res = await fetch(joinUrl(API_BASE, path), {
    method,
    headers,
    body: fetchBody,
  });

  const data = await safeJson(res);

  // ✅ If token expired, try refresh once and retry original request
  if (res.status === 401 && auth && retryOnAuth) {
    try {
      await refreshAccessToken();
      return apiFetch(path, { method, body, rawBody, auth, retryOnAuth: false, headers: customHeaders });
    } catch (e) {
      throw e;
    }
  }

  if (!res.ok) {
    throw buildError(res, data);
  }

  return data ?? {};
}
