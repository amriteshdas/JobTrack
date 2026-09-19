import api from "./api";

/**
 * Thin wrapper over the jobs endpoints. Every filter param is optional and
 * simply omitted from the query string when falsy -- axios's `params`
 * option drops undefined/empty values automatically via URLSearchParams
 * semantics only if we filter them ourselves first (axios does NOT drop
 * empty strings on its own), so we do that explicitly below.
 */
function cleanParams(params) {
  const out = {};
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      out[key] = value;
    }
  });
  return out;
}

export const jobsService = {
  async list(params = {}) {
    const { data } = await api.get("/jobs/", { params: cleanParams(params) });
    return data; // { count, next, previous, results }
  },

  async get(id) {
    const { data } = await api.get(`/jobs/${id}/`);
    return data;
  },

  async mine() {
    const { data } = await api.get("/jobs/mine/");
    return data;
  },
};

export const companiesService = {
  async list(params = {}) {
    const { data } = await api.get("/companies/", { params: cleanParams(params) });
    return data;
  },

  async get(slug) {
    const { data } = await api.get(`/companies/${slug}/`);
    return data;
  },

  async jobs(slug, params = {}) {
    const { data } = await api.get(`/companies/${slug}/jobs/`, {
      params: cleanParams(params),
    });
    return data;
  },
};
