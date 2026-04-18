import axios from "axios";

const DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const raw = localStorage.getItem("ai_interview_app_settings");

  let language = "en";

  if (raw) {
    try {
      const parsed = JSON.parse(raw);
      language = parsed.language || "en";
    } catch {}
  }

  config.headers["Accept-Language"] = language;
  return config;
});

export function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
  };
}