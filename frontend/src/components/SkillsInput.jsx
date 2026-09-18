import { useState } from "react";

export default function SkillsInput({ skills, onChange }) {
  const [draft, setDraft] = useState("");

  const addSkill = () => {
    const name = draft.trim();
    if (!name) return;
    // Case-insensitive de-dupe client-side too, so the chip list doesn't
    // show "Python" and "python" as two entries while the request is in
    // flight -- the server enforces the real de-dupe (Phase 5 backend).
    if (!skills.some((s) => s.toLowerCase() === name.toLowerCase())) {
      onChange([...skills, name]);
    }
    setDraft("");
  };

  const removeSkill = (name) => onChange(skills.filter((s) => s !== name));

  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkill();
    }
  };

  return (
    <div>
      <div className="flex flex-wrap gap-1.5 mb-2">
        {skills.map((name) => (
          <span
            key={name}
            className="inline-flex items-center gap-1 text-xs font-medium text-slate-700 bg-slate-100 rounded-full pl-2.5 pr-1.5 py-1"
          >
            {name}
            <button
              type="button"
              onClick={() => removeSkill(name)}
              className="text-slate-400 hover:text-slate-700"
              aria-label={`Remove ${name}`}
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add a skill and press Enter"
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
        />
        <button
          type="button"
          onClick={addSkill}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
        >
          Add
        </button>
      </div>
    </div>
  );
}
