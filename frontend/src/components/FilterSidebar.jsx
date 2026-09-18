const WORK_MODES = [
  { value: "", label: "Any" },
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

const EMPLOYMENT_TYPES = [
  { value: "", label: "Any" },
  { value: "full_time", label: "Full-time" },
  { value: "part_time", label: "Part-time" },
  { value: "internship", label: "Internship" },
  { value: "contract", label: "Contract" },
];

/**
 * Controlled by the parent (Home page holds the filter state), so this
 * component has no state of its own -- the URL/query-string is the single
 * source of truth, which means filters survive a page refresh or a shared
 * link "for free".
 */
export default function FilterSidebar({ filters, onChange }) {
  const set = (key, value) => onChange({ ...filters, [key]: value });

  return (
    <aside className="w-full lg:w-64 shrink-0 space-y-6">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          Location
        </label>
        <input
          type="text"
          value={filters.location || ""}
          onChange={(e) => set("location", e.target.value)}
          placeholder="e.g. Kolkata"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          Work mode
        </label>
        <div className="space-y-1.5">
          {WORK_MODES.map((opt) => (
            <RadioRow
              key={opt.value}
              name="work_mode"
              value={opt.value}
              label={opt.label}
              checked={(filters.work_mode || "") === opt.value}
              onChange={() => set("work_mode", opt.value)}
            />
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          Employment type
        </label>
        <div className="space-y-1.5">
          {EMPLOYMENT_TYPES.map((opt) => (
            <RadioRow
              key={opt.value}
              name="employment_type"
              value={opt.value}
              label={opt.label}
              checked={(filters.employment_type || "") === opt.value}
              onChange={() => set("employment_type", opt.value)}
            />
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          Minimum experience (years)
        </label>
        <input
          type="number"
          min="0"
          value={filters.experience_min || ""}
          onChange={(e) => set("experience_min", e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
        />
      </div>

      <button
        onClick={() => onChange({})}
        className="text-sm text-slate-500 hover:text-slate-900 hover:underline"
      >
        Clear all filters
      </button>
    </aside>
  );
}

function RadioRow({ name, value, label, checked, onChange }) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
      <input
        type="radio"
        name={name}
        value={value}
        checked={checked}
        onChange={onChange}
        className="accent-slate-900"
      />
      {label}
    </label>
  );
}
