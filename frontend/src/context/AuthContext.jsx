import { createContext, useContext, useEffect, useState } from "react";
import { authService } from "../services/auth";
import { tokenStore } from "../services/api";

const AuthContext = createContext(null);

/**
 * Holds the authenticated user for the whole app.
 *
 * Why `loading` exists and matters:
 * On a page refresh we have a token in localStorage but no user object yet,
 * so there is a moment where we genuinely do not know if the user is logged
 * in. Without a loading state, protected routes would see `user === null`
 * during that moment and bounce the user to /login on every refresh -- a
 * very common and very annoying SPA bug.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const bootstrap = async () => {
      if (!tokenStore.getAccess()) {
        setLoading(false);
        return;
      }
      try {
        setUser(await authService.me());
      } catch {
        tokenStore.clear();
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, []);

  const login = async (email, password) => {
    const u = await authService.login(email, password);
    setUser(u);
    return u;
  };

  const register = async (payload) => {
    const u = await authService.register(payload);
    setUser(u);
    return u;
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
    isJobSeeker: user?.role === "seeker",
    isEmployer: user?.role === "employer",
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an AuthProvider");
  return ctx;
}
