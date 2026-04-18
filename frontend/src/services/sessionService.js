import { apiClient, authHeaders } from "./apiClient";

export const sessionService = {
  async createSession(token, payload) {
    const { data } = await apiClient.post("/sessions/", payload, {
      headers: authHeaders(token),
    });
    return data;
  },

  async getMySessions(token) {
    const { data } = await apiClient.get("/sessions/", {
      headers: authHeaders(token),
    });
    return data;
  },

  async getSessionById(token, sessionId) {
    const { data } = await apiClient.get(`/sessions/${sessionId}`, {
      headers: authHeaders(token),
    });
    return data;
  },

  async getHistorySessions(token) {
    const { data } = await apiClient.get("/history/sessions", {
      headers: authHeaders(token),
    });
    return data;
  },

  async getScoreSummary(token, sessionId) {
    const { data } = await apiClient.get(`/history/scores/${sessionId}`, {
      headers: authHeaders(token),
    });
    return data;
  },
};