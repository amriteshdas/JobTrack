import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function Home() {
  const { user, isAuthenticated, logout, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center text-slate-400 text-sm">
        Loading…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center">
        <h1 className="text-2xl font-semibold text-slate-900">JobTrack</h1>
        <p className="mt-1 text-sm text-slate-500">Phase 2 — Authentication</p>

        {isAuthenticated ? (
          <>
            <p className="mt-6 text-sm text-slate-700">
              Signed in as <span className="font-medium">{user.email}</span>
              <br />
              <span className="text-xs text-slate-400 uppercase tracking-wide">
                {user.role}
              </span>
            </p>
            <div className="mt-5 flex gap-2 justify-center">
              <Link
                to={user.role === "employer" ? "/employer" : "/seeker"}
                className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm font-medium hover:bg-slate-800"
              >
                Go to dashboard
              </Link>
              <button
                onClick={logout}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Log out
              </button>
            </div>
          </>
        ) : (
          <div className="mt-6 flex gap-2 justify-center">
            <Link
              to="/login"
              className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm font-medium hover:bg-slate-800"
            >
              Sign in
            </Link>
            <Link
              to="/register"
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Create account
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
