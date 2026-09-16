import api, { tokenStore } from "./api";

export const authService = {
  async register(payload) {
    const { data } = await api.post("/auth/register/", payload);
    tokenStore.set(data.access, data.refresh);
    return data.user;
  },

  async login(email, password) {
    const { data } = await api.post("/auth/login/", { email, password });
    tokenStore.set(data.access, data.refresh);
    return data.user;
  },

  async logout() {
    const refresh = tokenStore.getRefresh();
    try {
      // Tell the server to blacklist the refresh token. If this fails
      // (network down, token already expired) we still clear locally --
      // the user asked to log out, so the UI must honour that regardless.
      if (refresh) await api.post("/auth/logout/", { refresh });
    } finally {
      tokenStore.clear();
    }
  },

  async me() {
    const { data } = await api.get("/auth/me/");
    return data.user;
  },
};
