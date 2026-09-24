import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import NotificationsBell from "./NotificationsBell";

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();

  const linkClass = ({ isActive }) =>
    `text-sm font-medium transition-colors ${
      isActive ? "text-violet-700" : "text-ink-700/80 hover:text-violet-700"
    }`;

  return (
    <header className="sticky top-0 z-20 border-b border-violet-100/70 bg-white/80 backdrop-blur-md supports-[backdrop-filter]:bg-white/70">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <span className="grid place-items-center h-8 w-8 rounded-lg bg-gradient-to-br from-violet-500 to-violet-700 text-white font-display font-bold text-sm shadow-[0_4px_12px_-2px_rgba(124,58,237,0.5)] transition-transform group-hover:scale-105">
            JT
          </span>
          <span className="font-display font-extrabold text-lg text-ink-950 tracking-tight">
            JobTrack
          </span>
        </Link>

        <nav className="flex items-center gap-5">
          {isAuthenticated ? (
            <>
              <NavLink to={user.role === "employer" ? "/employer" : "/seeker"} className={linkClass}>
                Dashboard
              </NavLink>
              {user.role === "seeker" && (
                <>
                  <NavLink to="/seeker/saved-jobs" className={linkClass}>
                    Saved
                  </NavLink>
                  <NavLink to="/seeker/applications" className={linkClass}>
                    Applications
                  </NavLink>
                  <NavLink to="/seeker/profile" className={linkClass}>
                    Profile
                  </NavLink>
                </>
              )}
              <NotificationsBell />
              <button onClick={logout} className="btn btn-secondary !py-1.5 !px-3 text-xs">
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-ink-700/80 hover:text-violet-700 transition-colors">
                Sign in
              </Link>
              <Link to="/register" className="btn btn-primary !py-2 !px-4 text-xs">
                Create account
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
