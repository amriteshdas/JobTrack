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
      {skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2.5">
          {skills.map((name) => (
            <span key={name} className="badge animate-pop pr-1.5">
              {name}
              <button
                type="button"
                onClick={() => removeSkill(name)}
                className="ml-1 h-4 w-4 rounded-full grid place-items-center text-violet-500 hover:bg-violet-200 hover:text-violet-800 transition-colors"
                aria-label={`Remove ${name}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add a skill and press Enter"
          className="input flex-1"
        />
        <button type="button" onClick={addSkill} className="btn btn-secondary">
          Add
        </button>
      </div>
    </div>
  );
}
