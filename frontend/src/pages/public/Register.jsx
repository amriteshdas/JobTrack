import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const ROLES = [
  { value: "seeker", label: "I'm looking for a job" },
  { value: "employer", label: "I'm hiring" },
];

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    password_confirm: "",
    role: "seeker",
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    setSubmitting(true);
    try {
      const user = await register(form);
      navigate(user.role === "employer" ? "/employer" : "/seeker", { replace: true });
    } catch (err) {
      // DRF returns field-keyed validation errors, so we can map them
      // straight onto the form instead of showing one generic message.
      setErrors(err.response?.data || { detail: "Something went wrong." });
    } finally {
      setSubmitting(false);
    }
  };

  const fieldError = (name) =>
    errors[name] && (
      <p className="mt-1 text-xs text-red-600 animate-fade-in">
        {Array.isArray(errors[name]) ? errors[name][0] : errors[name]}
      </p>
    );

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute -left-32 -top-32 h-80 w-80 rounded-full bg-violet-200/40 blur-3xl" />
      <div className="absolute -right-32 -bottom-32 h-80 w-80 rounded-full bg-sky-200/40 blur-3xl" />

      <div className="w-full max-w-md relative animate-fade-up">
        <Link to="/" className="flex items-center justify-center gap-2 mb-1">
          <span className="grid place-items-center h-9 w-9 rounded-lg bg-gradient-to-br from-violet-500 to-violet-700 text-white font-display font-bold text-sm shadow-soft">
            JT
          </span>
          <span className="font-display font-extrabold text-xl text-ink-950">JobTrack</span>
        </Link>
        <h1 className="mt-2 text-sm text-ink-500 text-center">Create your account</h1>

        <form onSubmit={handleSubmit} className="mt-6 card p-6 space-y-4">
          {errors.detail && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700 animate-pop">
              {errors.detail}
            </div>
          )}

          <div>
            <span className="field-label mb-2">I am…</span>
            <div className="grid grid-cols-2 gap-2">
              {ROLES.map((r) => (
                <button
                  key={r.value}
                  type="button"
                  onClick={() => setForm({ ...form, role: r.value })}
                  className={`rounded-lg border px-3 py-2.5 text-sm font-medium text-left transition-all ${
                    form.role === r.value
                      ? "border-violet-600 bg-violet-600 text-white shadow-soft"
                      : "border-violet-100 text-ink-700 hover:border-violet-300 hover:bg-violet-50"
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
            {fieldError("role")}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="field-label">First name</label>
              <input name="first_name" value={form.first_name} onChange={update} className="input" />
            </div>
            <div>
              <label className="field-label">Last name</label>
              <input name="last_name" value={form.last_name} onChange={update} className="input" />
            </div>
          </div>

          <div>
            <label className="field-label">Email</label>
            <input type="email" name="email" required value={form.email} onChange={update} className="input" />
            {fieldError("email")}
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
            {fieldError("password")}
          </div>

          <div>
            <label className="field-label">Confirm password</label>
            <input
              type="password"
              name="password_confirm"
              required
              value={form.password_confirm}
              onChange={update}
              className="input"
            />
            {fieldError("password_confirm")}
          </div>

          <button type="submit" disabled={submitting} className="btn btn-primary w-full">
            {submitting ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-ink-500">
          Already have an account?{" "}
          <Link to="/login" className="text-violet-700 font-semibold hover:text-violet-800">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
