import api from "./api";

export const interviewsService = {
  async schedule(applicationId, payload) {
    const { data } = await api.post(`/applications/${applicationId}/interviews/`, payload);
    return data;
  },

  async mine() {
    const { data } = await api.get("/interviews/mine/");
    return data;
  },

  async update(interviewId, payload) {
    const { data } = await api.patch(`/interviews/${interviewId}/`, payload);
    return data;
  },
};
