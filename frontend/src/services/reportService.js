import { apiClient, authHeaders } from "./apiClient";

export const reportService = {
  async getReport(token, sessionId) {
    const { data } = await apiClient.get(`/reports/${sessionId}`, {
      headers: authHeaders(token),
    });
    return data;
  },
};