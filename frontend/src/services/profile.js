import api from "./api";

export const profileService = {
  async getSeekerProfile() {
    const { data } = await api.get("/profiles/seeker/me/");
    return data;
  },

  async updateSeekerProfile(payload) {
    // multipart/form-data whenever a File is present (resume/photo), plain
    // JSON otherwise -- axios picks the right serialization automatically
    // once we hand it a FormData object, but we only want that overhead
    // when there's actually a file to send.
    const hasFile = Object.values(payload).some((v) => v instanceof File);
    if (!hasFile) {
      const { data } = await api.patch("/profiles/seeker/me/", payload);
      return data;
    }
    const form = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== undefined && value !== null) form.append(key, value);
    });
    const { data } = await api.patch("/profiles/seeker/me/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async setSkills(skillNames) {
    const { data } = await api.put("/profiles/seeker/me/skills/", { skills: skillNames });
    return data;
  },

  async addEducation(payload) {
    const { data } = await api.post("/profiles/seeker/me/education/", payload);
    return data;
  },

  async updateEducation(id, payload) {
    const { data } = await api.patch(`/profiles/seeker/me/education/${id}/`, payload);
    return data;
  },

  async deleteEducation(id) {
    await api.delete(`/profiles/seeker/me/education/${id}/`);
  },

  async addExperience(payload) {
    const { data } = await api.post("/profiles/seeker/me/experience/", payload);
    return data;
  },

  async updateExperience(id, payload) {
    const { data } = await api.patch(`/profiles/seeker/me/experience/${id}/`, payload);
    return data;
  },

  async deleteExperience(id) {
    await api.delete(`/profiles/seeker/me/experience/${id}/`);
  },
};

export const savedJobsService = {
  async list() {
    const { data } = await api.get("/saved-jobs/");
    return data;
  },

  async save(jobId) {
    const { data } = await api.post("/saved-jobs/", { job: jobId });
    return data;
  },

  async unsave(jobId) {
    await api.delete(`/saved-jobs/${jobId}/`);
  },
};
