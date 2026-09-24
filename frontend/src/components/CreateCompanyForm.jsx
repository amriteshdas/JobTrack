import { useState } from "react";
import { companiesService } from "../services/jobs";

/**
 * An employer must be a member of a company before they can post a job
 * (enforced server-side since Phase 3). Rather than sending a brand-new
 * employer with zero companies to a dead end, CreateJob renders this first
 * and only shows the job form once a company exists.
 */
export default function CreateCompanyForm({ onCreated }) {
  const [form, setForm] = useState({ name: "", location: "", industry: "" });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const company = await companiesService.create(form);
      onCreated(company);
    } catch (err) {
      setError(err.response?.data?.name?.[0] || "Could not create the company.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card p-6 animate-fade-up">
      <h2 className="font-display text-base font-bold text-ink-950">Set up your company first</h2>
      <p className="mt-1 text-sm text-ink-500">
        You need a company before you can post a job. This only takes a moment -- you can add
        more details later.
      </p>

      <form onSubmit={submit} className="mt-5 space-y-3">
        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700 animate-pop">
            {error}
          </div>
        )}
        <input
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          placeholder="Company name"
          required
          className="input"
        />
        <input
          value={form.location}
          onChange={(e) => setForm({ ...form, location: e.target.value })}
          placeholder="Location (optional)"
          className="input"
        />
        <input
          value={form.industry}
          onChange={(e) => setForm({ ...form, industry: e.target.value })}
          placeholder="Industry (optional)"
          className="input"
        />
        <button type="submit" disabled={submitting} className="btn btn-primary">
          {submitting ? "Creating…" : "Create company"}
        </button>
      </form>
    </div>
  );
}
