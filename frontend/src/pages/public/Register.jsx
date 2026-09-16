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
      <p className="mt-1 text-xs text-red-600">
        {Array.isArray(errors[name]) ? errors[name][0] : errors[name]}
      </p>
    );

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <h1 className="text-2xl font-semibold text-slate-900 text-center">
          Create your JobTrack account
        </h1>

        <form
          onSubmit={handleSubmit}
          className="mt-6 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4"
        >
          {errors.detail && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
              {errors.detail}
            </div>
          )}

          <div>
            <span className="block text-sm font-medium text-slate-700 mb-2">
              I am…
            </span>
            <div className="grid grid-cols-2 gap-2">
              {ROLES.map((r) => (
                <button
                  key={r.value}
                  type="button"
                  onClick={() => setForm({ ...form, role: r.value })}
                  className={`rounded-lg border px-3 py-2.5 text-sm text-left transition ${
                    form.role === r.value
                      ? "border-slate-900 bg-slate-900 text-white"
                      : "border-slate-300 text-slate-700 hover:border-slate-400"
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
              <label className="block text-sm font-medium text-slate-700 mb-1">
                First name
              </label>
              <input
                name="first_name"
                value={form.first_name}
                onChange={update}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Last name
              </label>
              <input
                name="last_name"
                value={form.last_name}
                onChange={update}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Email
            </label>
            <input
              type="email"
              name="email"
              required
              value={form.email}
              onChange={update}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
            />
            {fieldError("email")}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Password
            </label>
            <input
              type="password"
              name="password"
              required
              value={form.password}
              onChange={update}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
            />
            {fieldError("password")}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Confirm password
            </label>
            <input
              type="password"
              name="password_confirm"
              required
              value={form.password_confirm}
              onChange={update}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
            />
            {fieldError("password_confirm")}
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-slate-900 text-white text-sm font-medium py-2.5 hover:bg-slate-800 disabled:opacity-50 transition"
          >
            {submitting ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="text-slate-900 font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
