import { useAuth } from "../../context/AuthContext";

// Placeholder only. The real dashboard is Phase 7. This exists so Phase 2
// can demonstrate that role-based routing actually sends users to the right
// place and blocks the wrong ones.
export default function SeekerDashboard() {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-2xl mx-auto bg-white border border-slate-200 rounded-2xl p-6">
        <p className="text-xs uppercase tracking-wide text-slate-400">Job Seeker</p>
        <h1 className="mt-1 text-xl font-semibold text-slate-900">
          Welcome, {user.full_name || user.email}
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Your dashboard gets built in Phase 7. For now this page proves that
          authentication, role routing, and token persistence all work.
        </p>
        <button
          onClick={logout}
          className="mt-5 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Log out
        </button>
      </div>
    </div>
  );
}
