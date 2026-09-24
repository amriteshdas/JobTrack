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
    <aside className="w-full lg:w-64 shrink-0">
      <div className="card p-5 space-y-6 lg:sticky lg:top-24">
        <div className="flex items-center justify-between">
          <h2 className="font-display font-bold text-ink-950 text-sm">Filters</h2>
          <button onClick={() => onChange({})} className="text-xs font-medium text-violet-600 hover:text-violet-800 transition-colors">
            Clear all
          </button>
        </div>

        <div>
          <label className="field-label">Location</label>
          <input
            type="text"
            value={filters.location || ""}
            onChange={(e) => set("location", e.target.value)}
            placeholder="e.g. Kolkata"
            className="input"
          />
        </div>

        <div>
          <label className="field-label">Work mode</label>
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
          <label className="field-label">Employment type</label>
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
          <label className="field-label">Minimum experience (years)</label>
          <input
            type="number"
            min="0"
            value={filters.experience_min || ""}
            onChange={(e) => set("experience_min", e.target.value)}
            className="input"
          />
        </div>
      </div>
    </aside>
  );
}

function RadioRow({ name, value, label, checked, onChange }) {
  return (
    <label className="flex items-center gap-2.5 text-sm text-ink-700 cursor-pointer group">
      <span className="relative grid place-items-center h-4 w-4 shrink-0">
        <input
          type="radio"
          name={name}
          value={value}
          checked={checked}
          onChange={onChange}
          className="peer sr-only"
        />
        <span className="h-4 w-4 rounded-full border-2 border-violet-200 peer-checked:border-violet-600 transition-colors" />
        <span className="absolute h-2 w-2 rounded-full bg-violet-600 scale-0 peer-checked:scale-100 transition-transform" />
      </span>
      <span className={checked ? "text-ink-950 font-medium" : "group-hover:text-ink-950 transition-colors"}>
        {label}
      </span>
    </label>
  );
}
