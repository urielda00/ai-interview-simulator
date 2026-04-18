import axios from "axios";
import { apiClient, authHeaders } from "./apiClient";

export const uploadService = {
  async uploadProjectFile(token, sessionId, file) {
    const formData = new FormData();
    formData.append("file", file);

    const { data } = await axios.post(
      `${apiClient.defaults.baseURL}/uploads/project-files/${sessionId}`,
      formData,
      {
        headers: {
          ...authHeaders(token),
          "Content-Type": "multipart/form-data",
        },
      }
    );

    return data;
  },

  async getProjectFiles(token, sessionId) {
    const { data } = await apiClient.get(`/uploads/project-files/${sessionId}`, {
      headers: authHeaders(token),
    });
    return data;
  },
};