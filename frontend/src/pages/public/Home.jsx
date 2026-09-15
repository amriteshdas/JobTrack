import { useEffect, useState } from "react";
import api from "../../services/api";

/**
 * This is NOT the real JobTrack home page (that's Phase 4). It exists only
 * to prove, visually, that:
 *   1. React + Vite are rendering
 *   2. Tailwind classes are being compiled and applied
 *   3. Axios can reach the Django backend across CORS
 * Every one of those is a separate thing that can silently be broken, so
 * we prove all three together instead of assuming they work individually.
 */
export default function Home() {
  const [status, setStatus] = useState("checking...");
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .get("/health/")
      .then((res) => setStatus(res.data.status))
      .catch((err) => {
        setError(err.message);
        setStatus("unreachable");
      });
  }, []);

  const isOk = status === "ok";

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center">
        <h1 className="text-2xl font-semibold text-slate-900">JobTrack</h1>
        <p className="mt-1 text-sm text-slate-500">
          Project foundation — Phase 1
        </p>

        <div className="mt-6 flex items-center justify-center gap-2">
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              isOk ? "bg-emerald-500" : "bg-amber-500"
            }`}
          />
          <span className="text-sm font-medium text-slate-700">
            Backend status: {status}
          </span>
        </div>

        {error && (
          <p className="mt-3 text-xs text-red-500">
            {error} — is the Django dev server running on :8000?
          </p>
        )}

        <p className="mt-6 text-xs text-slate-400">
          React + Vite + Tailwind v4 + Axios → Django + DRF + PostgreSQL
        </p>
      </div>
    </div>
  );
}
