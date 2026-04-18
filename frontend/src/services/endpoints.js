export const ENDPOINTS = {
  health: "/api/v1/health/",
  register: "/api/v1/auth/register",
  getUser: (userId) => `/api/v1/auth/${userId}`,

  createSession: "/api/v1/sessions/",
  getSession: (sessionId) => `/api/v1/sessions/${sessionId}`,

  startInterview: "/api/v1/interviews/start",
  answerInterview: "/api/v1/interviews/answer",
  getTranscript: (sessionId) => `/api/v1/interviews/transcript/${sessionId}`,

  getReport: (sessionId) => `/api/v1/reports/${sessionId}`,
};