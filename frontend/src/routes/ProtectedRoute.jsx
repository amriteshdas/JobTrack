import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Client-side route protection.
 *
 * Be clear about what this is and is not: this is a UX control, NOT a
 * security control. Anyone can edit JavaScript in their browser and render
 * whatever component they want. The only thing actually protecting data is
 * the backend permission check on each API call -- which is exactly why
 * Phase 2 tested those server-side with a forged role claim.
 *
 * What this DOES buy: users do not see broken pages full of 403 errors,
 * and they land somewhere sensible when their session expires.
 */
export default function ProtectedRoute({ children, role }) {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center bg-canvas">
        <div className="flex items-center gap-2.5 text-ink-500 text-sm">
          <span className="h-4 w-4 rounded-full border-2 border-violet-200 border-t-violet-600 animate-spin" />
          Loading…
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Remember where they were headed so login can send them back.
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (role && user.role !== role) {
    return <Navigate to="/" replace />;
  }

  return children;
}
