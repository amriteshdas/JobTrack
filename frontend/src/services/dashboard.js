import api from "./api";

export const dashboardService = {
  async seeker() {
    const { data } = await api.get("/dashboard/seeker/");
    return data;
  },

  async employer() {
    const { data } = await api.get("/dashboard/employer/");
    return data;
  },
};
