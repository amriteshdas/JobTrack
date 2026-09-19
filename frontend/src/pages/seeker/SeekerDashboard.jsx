import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

// Still a placeholder for the real analytics dashboard (Phase 7: application
// counts, recent activity, recommended jobs). What's real as of Phase 5:
// the links to Profile and Saved Jobs actually go somewhere now.
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
          Application tracking and stats arrive in Phase 7. For now:
        </p>
        <div className="mt-4 flex gap-3">
          <Link
            to="/seeker/profile"
            className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm font-medium hover:bg-slate-800"
          >
            Edit profile
          </Link>
          <Link
            to="/seeker/saved-jobs"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Saved jobs
          </Link>
          <Link
            to="/seeker/applications"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            My applications
          </Link>
        </div>
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
