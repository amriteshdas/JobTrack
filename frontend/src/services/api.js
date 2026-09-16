import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
  headers: { "Content-Type": "application/json" },
});

// ---------------------------------------------------------------------------
// Token storage
// ---------------------------------------------------------------------------
// localStorage is used here for simplicity. The honest tradeoff: tokens in
// localStorage are readable by any JavaScript running on the page, so an XSS
// vulnerability becomes a token theft. The more secure alternative is
// httpOnly cookies, which JS cannot read -- but that requires CSRF protection
// and cookie/CORS configuration that complicates a cross-origin SPA setup.
// Given short-lived access tokens (15 min) and rotated refresh tokens, this
// is a reasonable MVP choice, and it is the kind of tradeoff worth being able
// to articulate rather than defaulting into silently.

const ACCESS_KEY = "jobtrack_access";
const REFRESH_KEY = "jobtrack_refresh";

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access, refresh) => {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

// ---------------------------------------------------------------------------
// Request interceptor: attach the access token to every outgoing request
// ---------------------------------------------------------------------------
api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ---------------------------------------------------------------------------
// Response interceptor: silent refresh on 401
// ---------------------------------------------------------------------------
// When an access token expires mid-session the user should not be kicked out.
// On a 401 we exchange the refresh token for a new access token once, then
// replay the original request.
//
// Two details that matter:
//  - `_retry` guards against an infinite loop if the refresh itself 401s.
//  - Concurrent 401s are queued so that N parallel failed requests trigger
//    exactly ONE refresh call, not N of them. With rotation enabled, firing
//    several refreshes at once would blacklist each other's tokens and log
//    the user out -- a genuinely confusing bug to debug later.

let isRefreshing = false;
let queue = [];

const processQueue = (error, token = null) => {
  queue.forEach((p) => (error ? p.reject(error) : p.resolve(token)));
  queue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    const refresh = tokenStore.getRefresh();
    if (!refresh) {
      tokenStore.clear();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        queue.push({ resolve, reject });
      }).then((token) => {
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      });
    }

    original._retry = true;
    isRefreshing = true;

    try {
      // Bare axios, not `api` -- using `api` here would recurse through
      // this same interceptor on failure.
      const { data } = await axios.post(
        `${api.defaults.baseURL}/auth/refresh/`,
        { refresh },
      );
      tokenStore.set(data.access, data.refresh);
      processQueue(null, data.access);
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch (refreshError) {
      processQueue(refreshError, null);
      tokenStore.clear();
      window.location.href = "/login";
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export default api;
