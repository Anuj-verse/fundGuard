const rawApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ??
  import.meta.env.VITE_DASHBOARD_API_BASE_URL ??
  "http://localhost:8005";

export const API_BASE_URL = rawApiBaseUrl.replace(/\/$/, "");
export const WS_URL = import.meta.env.VITE_WS_URL ?? `${API_BASE_URL.replace(/^http/i, "ws")}/ws`;
