// apps/web/src/lib/api/client.ts
import axios from "axios";
import { getCookie } from "./authTokens";

const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

// Authorization ヘッダーと CSRF だけ付与（GET/HEAD/OPTIONS 以外）
api.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};

  const accessToken = getCookie("access_token");
  if (accessToken) {
    (config.headers as any).Authorization = `Bearer ${accessToken}`;
  }

  const method = (config.method || "get").toLowerCase();
  if (!["get", "head", "options"].includes(method)) {
    const token = getCookie("csrftoken");
    if (token) {
      (config.headers as any)["X-CSRFToken"] = token;
    }
  }
  return config;
});

export default api;
