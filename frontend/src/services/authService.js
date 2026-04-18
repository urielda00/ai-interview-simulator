import { apiClient, authHeaders } from "./apiClient";

export const authService = {
  async register(payload) {
    const { data } = await apiClient.post("/auth/register", payload);
    return data;
  },

  async login(payload) {
    const { data } = await apiClient.post("/auth/login", payload);
    return data;
  },

  async getMe(token) {
    const { data } = await apiClient.get("/auth/me", {
      headers: authHeaders(token),
    });
    return data;
  },
};