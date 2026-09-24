import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await login(form.email, form.password);
      const from = location.state?.from?.pathname;
      navigate(from || (user.role === "employer" ? "/employer" : "/seeker"), {
        replace: true,
      });
    } catch (err) {
      // Deliberately generic. The backend returns 401 for both "no such
      // account" and "wrong password", and we keep it that way: telling an
      // attacker which emails are registered is free reconnaissance.
      setError(
        err.response?.status === 401
          ? "Invalid email or password."
          : "Something went wrong. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute -left-32 -top-32 h-80 w-80 rounded-full bg-violet-200/40 blur-3xl" />
      <div className="absolute -right-32 -bottom-32 h-80 w-80 rounded-full bg-sky-200/40 blur-3xl" />

      <div className="w-full max-w-sm relative animate-fade-up">
        <Link to="/" className="flex items-center justify-center gap-2 mb-1">
          <span className="grid place-items-center h-9 w-9 rounded-lg bg-gradient-to-br from-violet-500 to-violet-700 text-white font-display font-bold text-sm shadow-soft">
            JT
          </span>
          <span className="font-display font-extrabold text-xl text-ink-950">JobTrack</span>
        </Link>
        <p className="mt-2 text-sm text-ink-500 text-center">Sign in to your account</p>

        <form onSubmit={handleSubmit} className="mt-6 card p-6 space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700 animate-pop">
              {error}
            </div>
          )}

          <div>
            <label className="field-label">Email</label>
            <input type="email" name="email" required value={form.email} onChange={update} className="input" />
          </div>

          <div>
            <label className="field-label">Password</label>
            <input
              type="password"
              name="password"
              required
              value={form.password}
              onChange={update}
              className="input"
            />
          </div>

          <button type="submit" disabled={submitting} className="btn btn-primary w-full">
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-ink-500">
          No account?{" "}
          <Link to="/register" className="text-violet-700 font-semibold hover:text-violet-800">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
