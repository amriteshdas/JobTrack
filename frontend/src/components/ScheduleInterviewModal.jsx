import { useState } from "react";
import { interviewsService } from "../services/interviews";

const TYPES = [
  { value: "phone", label: "Phone" },
  { value: "video", label: "Video" },
  { value: "onsite", label: "Onsite" },
];

export default function ScheduleInterviewModal({ applicationId, onClose, onScheduled }) {
  const [type, setType] = useState("video");
  const [scheduledAt, setScheduledAt] = useState("");
  const [meetingLink, setMeetingLink] = useState("");
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await interviewsService.schedule(applicationId, {
        interview_type: type,
        scheduled_at: new Date(scheduledAt).toISOString(),
        meeting_link: type === "onsite" ? "" : meetingLink,
        location: type === "onsite" ? location : "",
        notes,
      });
      onScheduled();
    } catch (err) {
      const data = err.response?.data;
      setError(
        data?.detail ||
          data?.scheduled_at?.[0] ||
          data?.non_field_errors?.[0] ||
          "Could not schedule this interview."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-ink-950/40 backdrop-blur-sm flex items-center justify-center p-4 z-30 animate-fade-in">
      <div className="card p-6 max-w-md w-full animate-pop shadow-lift">
        <h2 className="font-display text-lg font-bold text-ink-950">Schedule interview</h2>

        <form onSubmit={submit} className="mt-4 space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700 animate-pop">
              {error}
            </div>
          )}

          <div>
            <label className="field-label">Type</label>
            <div className="grid grid-cols-3 gap-2">
              {TYPES.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setType(t.value)}
                  className={`rounded-lg border px-3 py-2 text-sm font-medium transition-all ${
                    type === t.value
                      ? "border-violet-600 bg-violet-600 text-white shadow-soft"
                      : "border-violet-100 text-ink-700 hover:border-violet-300 hover:bg-violet-50"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="field-label">Date and time</label>
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              required
              className="input"
            />
          </div>

          {type === "onsite" ? (
            <div>
              <label className="field-label">Location</label>
              <input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Office address"
                required
                className="input"
              />
            </div>
          ) : (
            <div>
              <label className="field-label">Meeting link</label>
              <input
                type="url"
                value={meetingLink}
                onChange={(e) => setMeetingLink(e.target.value)}
                placeholder="https://..."
                required
                className="input"
              />
            </div>
          )}

          <div>
            <label className="field-label">Notes (optional)</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="input resize-none"
            />
          </div>

          <div className="flex gap-2 justify-end pt-1">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="btn btn-primary">
              {submitting ? "Scheduling…" : "Schedule"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
