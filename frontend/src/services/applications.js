import api from "./api";

export const applicationsService = {
  async apply(jobId, { resume, coverLetter }) {
    const form = new FormData();
    // `resume` is optional here -- omitting it entirely (not even an empty
    // field) tells the backend to fall back to the seeker's profile resume.
    // Appending an empty string would NOT do the same thing: DRF's
    // FileField sees an empty value as "a blank file was submitted", not
    // "no file was submitted", and rejects it.
    if (resume) form.append("resume", resume);
    if (coverLetter) form.append("cover_letter", coverLetter);
    const { data } = await api.post(`/jobs/${jobId}/apply/`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async mine() {
    const { data } = await api.get("/applications/mine/");
    return data;
  },

  async withdraw(applicationId) {
    const { data } = await api.post(`/applications/${applicationId}/withdraw/`);
    return data;
  },

  async applicantsForJob(jobId) {
    const { data } = await api.get(`/jobs/${jobId}/applicants/`);
    return data;
  },

  async setStatus(applicationId, statusValue) {
    const { data } = await api.patch(`/applications/${applicationId}/status/`, {
      status: statusValue,
    });
    return data;
  },
};

export const notificationsService = {
  async list() {
    const { data } = await api.get("/notifications/");
    return data;
  },

  async markRead(id) {
    const { data } = await api.patch(`/notifications/${id}/read/`);
    return data;
  },
};
