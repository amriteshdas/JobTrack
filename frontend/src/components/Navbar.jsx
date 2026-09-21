import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import NotificationsBell from "./NotificationsBell";

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link to="/" className="font-semibold text-slate-900">
          JobTrack
        </Link>

        <nav className="flex items-center gap-4 text-sm">
          {isAuthenticated ? (
            <>
              <Link
                to={user.role === "employer" ? "/employer" : "/seeker"}
                className="text-slate-600 hover:text-slate-900"
              >
                Dashboard
              </Link>
              {user.role === "seeker" && (
                <Link to="/seeker/profile" className="text-slate-600 hover:text-slate-900">
                  Profile
                </Link>
              )}
              <NotificationsBell />
              <button onClick={logout} className="text-slate-600 hover:text-slate-900">
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-slate-600 hover:text-slate-900">
                Sign in
              </Link>
              <Link
                to="/register"
                className="rounded-lg bg-slate-900 text-white px-3 py-1.5 hover:bg-slate-800"
              >
                Create account
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
