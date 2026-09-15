import axios from "axios";

// A single shared axios instance instead of calling axios.get/.post directly
// from components. Every page/service imports THIS, so when auth headers
// (Phase 2) and refresh-token interceptors get added, every request gets
// them automatically without touching call sites all over the app.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;
