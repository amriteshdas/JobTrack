import { useState } from "react";
import SkillsInput from "./SkillsInput";

const WORK_MODES = [
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

const EMPLOYMENT_TYPES = [
  { value: "full_time", label: "Full-time" },
  { value: "part_time", label: "Part-time" },
  { value: "internship", label: "Internship" },
  { value: "contract", label: "Contract" },
];

const emptyForm = {
  company: "",
  title: "",
  description: "",
  responsibilities: "",
  qualifications: "",
  benefits: "",
  location: "",
  work_mode: "remote",
  employment_type: "full_time",
  experience_required: 0,
  salary_min: "",
  salary_max: "",
  application_deadline: "",
  skills: [],
};

/**
 * Shared between CreateJob and EditJob -- both need the exact same fields
 * and the exact same validation feedback shape (DRF's field-keyed errors),
 * so one form with an `initial` prop and an `onSubmit` callback avoids
 * maintaining two near-identical field lists that would inevitably drift.
 */
export default function JobForm({ companies, initial, onSubmit, submitLabel }) {
  const [form, setForm] = useState({ ...emptyForm, ...initial });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const set = (field, value) => setForm({ ...form, [field]: value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    setSubmitting(true);
    try {
      await onSubmit({
        ...form,
        company: Number(form.company),
        salary_min: form.salary_min === "" ? null : Number(form.salary_min),
        salary_max: form.salary_max === "" ? null : Number(form.salary_max),
        experience_required: Number(form.experience_required) || 0,
        application_deadline: form.application_deadline || null,
      });
    } catch (err) {
      setErrors(err.response?.data || { detail: "Something went wrong. Please try again." });
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
    <form onSubmit={handleSubmit} className="space-y-5">
      {errors.detail && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
          {errors.detail}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Company</label>
        <select
          value={form.company}
          onChange={(e) => set("company", e.target.value)}
          required
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
        >
          <option value="" disabled>
            Select a company…
          </option>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        {fieldError("company")}
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Job title</label>
        <input
          value={form.title}
          onChange={(e) => set("title", e.target.value)}
          required
          placeholder="e.g. Backend Engineer"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
        />
        {fieldError("title")}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Location</label>
          <input
            value={form.location}
            onChange={(e) => set("location", e.target.value)}
            required
            placeholder="e.g. Kolkata"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
          />
          {fieldError("location")}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Experience required (years)
          </label>
          <input
            type="number"
            min="0"
            value={form.experience_required}
            onChange={(e) => set("experience_required", e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Work mode</label>
          <select
            value={form.work_mode}
            onChange={(e) => set("work_mode", e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
          >
            {WORK_MODES.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Employment type</label>
          <select
            value={form.employment_type}
            onChange={(e) => set("employment_type", e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
          >
            {EMPLOYMENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Salary min (optional)
          </label>
          <input
            type="number"
            min="0"
            value={form.salary_min}
            onChange={(e) => set("salary_min", e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Salary max (optional)
          </label>
          <input
            type="number"
            min="0"
            value={form.salary_max}
            onChange={(e) => set("salary_max", e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
          />
          {fieldError("salary_max")}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Application deadline (optional)
        </label>
        <input
          type="date"
          value={form.application_deadline || ""}
          onChange={(e) => set("application_deadline", e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
        />
        {fieldError("application_deadline")}
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Skills</label>
        <SkillsInput skills={form.skills} onChange={(skills) => set("skills", skills)} />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
        <textarea
          value={form.description}
          onChange={(e) => set("description", e.target.value)}
          rows={5}
          required
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
        />
        {fieldError("description")}
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Responsibilities (optional)
        </label>
        <textarea
          value={form.responsibilities}
          onChange={(e) => set("responsibilities", e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Qualifications (optional)
        </label>
        <textarea
          value={form.qualifications}
          onChange={(e) => set("qualifications", e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Benefits (optional)
        </label>
        <textarea
          value={form.benefits}
          onChange={(e) => set("benefits", e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
        />
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="rounded-lg bg-slate-900 text-white px-5 py-2.5 text-sm font-medium hover:bg-slate-800 disabled:opacity-50"
      >
        {submitting ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}
