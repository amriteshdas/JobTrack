import { useEffect, useState } from "react";
import { applicationsService } from "../services/applications";
import { profileService } from "../services/profile";

function filenameFromUrl(url) {
  if (!url) return "";
  try {
    return decodeURIComponent(url.split("/").pop());
  } catch {
    return url;
  }
}

export default function ApplyModal({ jobId, onClose, onApplied }) {
  const [defaultResumeUrl, setDefaultResumeUrl] = useState(undefined); // undefined = still loading
  const [useDefault, setUseDefault] = useState(true);
  const [overrideFile, setOverrideFile] = useState(null);
  const [coverLetter, setCoverLetter] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Load the seeker's profile once, just to find out whether a default
  // resume exists and what it's called -- not to re-download the file
  // itself. If they don't change anything, the actual file is never
  // fetched by the browser at all; the backend copies it server-side.
  useEffect(() => {
    let cancelled = false;
    profileService
      .getSeekerProfile()
      .then((profile) => {
        if (!cancelled) {
          setDefaultResumeUrl(profile.resume || null);
          // No default on file -> the "use default" toggle makes no sense,
          // go straight to requiring an upload.
          setUseDefault(!!profile.resume);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDefaultResumeUrl(null);
          setUseDefault(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const hasDefault = !!defaultResumeUrl;
  const needsUpload = !hasDefault || !useDefault;

  const submit = async (e) => {
    e.preventDefault();
    if (needsUpload && !overrideFile) {
      setError("Please attach a resume (PDF or Word document).");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await applicationsService.apply(jobId, {
        // Omitted entirely when using the default -- the backend fills it
        // in from the profile resume. Only sent when the seeker chose to
        // override it for this specific application.
        resume: needsUpload ? overrideFile : null,
        coverLetter,
      });
      onApplied();
    } catch (err) {
      const data = err.response?.data;
      setError(data?.detail || data?.resume?.[0] || "Could not submit your application.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-ink-950/40 backdrop-blur-sm flex items-center justify-center p-4 z-30 animate-fade-in">
      <div className="card p-6 max-w-md w-full animate-pop shadow-lift">
        <h2 className="font-display text-lg font-bold text-ink-950">Apply for this role</h2>

        <form onSubmit={submit} className="mt-4 space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700 animate-pop">
              {error}
            </div>
          )}

          <div>
            <label className="field-label">Resume</label>

            {defaultResumeUrl === undefined && (
              <p className="text-sm text-ink-500">Checking your profile…</p>
            )}

            {defaultResumeUrl !== undefined && hasDefault && useDefault && (
              <div className="flex items-center justify-between rounded-lg border border-violet-100 bg-violet-50/60 px-3 py-2">
                <span className="text-sm text-ink-700 truncate">
                  Using your uploaded resume: <strong className="text-ink-950">{filenameFromUrl(defaultResumeUrl)}</strong>
                </span>
                <button
                  type="button"
                  onClick={() => setUseDefault(false)}
                  className="shrink-0 text-sm font-medium text-violet-600 hover:text-violet-800 ml-2"
                >
                  Change
                </button>
              </div>
            )}

            {defaultResumeUrl !== undefined && needsUpload && (
              <div>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => setOverrideFile(e.target.files[0] || null)}
                  className="text-sm text-ink-700 file:mr-3 file:rounded-lg file:border-0 file:bg-violet-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-violet-700 hover:file:bg-violet-100"
                />
                {hasDefault && (
                  <button
                    type="button"
                    onClick={() => {
                      setUseDefault(true);
                      setOverrideFile(null);
                    }}
                    className="block mt-2 text-sm font-medium text-violet-600 hover:text-violet-800"
                  >
                    Use my uploaded resume instead
                  </button>
                )}
                {!hasDefault && (
                  <p className="mt-1.5 text-xs text-ink-500">
                    Tip: add a resume to your profile once and it'll be used by default on future
                    applications.
                  </p>
                )}
              </div>
            )}
          </div>

          <div>
            <label className="field-label">Cover letter (optional)</label>
            <textarea
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              rows={5}
              className="input resize-none"
              placeholder="Why are you a good fit for this role?"
            />
          </div>

          <div className="flex gap-2 justify-end pt-1">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || defaultResumeUrl === undefined}
              className="btn btn-primary"
            >
              {submitting ? "Submitting…" : "Submit application"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
