import { apiClient, authHeaders } from "./apiClient";

export const interviewService = {
  async startInterview(token, session_id) {
    const { data } = await apiClient.post(
      "/interviews/start",
      { session_id },
      { headers: authHeaders(token) }
    );
    return data;
  },

  async answerInterview(token, payload) {
    const { data } = await apiClient.post("/interviews/answer", payload, {
      headers: authHeaders(token),
    });
    return data;
  },

  async finishInterview(token, sessionId) {
    const { data } = await apiClient.post(
      `/interviews/finish/${sessionId}`,
      {},
      {
        headers: authHeaders(token),
      }
    );
    return data;
  },

  async getTranscript(token, sessionId) {
    const { data } = await apiClient.get(`/interviews/transcript/${sessionId}`, {
      headers: authHeaders(token),
    });
    return data;
  },
};