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
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-20">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full">
        <h2 className="text-lg font-semibold text-slate-900">Apply for this role</h2>

        <form onSubmit={submit} className="mt-4 space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Resume</label>

            {defaultResumeUrl === undefined && (
              <p className="text-sm text-slate-400">Checking your profile…</p>
            )}

            {defaultResumeUrl !== undefined && hasDefault && useDefault && (
              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                <span className="text-sm text-slate-700 truncate">
                  Using your uploaded resume: <strong>{filenameFromUrl(defaultResumeUrl)}</strong>
                </span>
                <button
                  type="button"
                  onClick={() => setUseDefault(false)}
                  className="shrink-0 text-sm text-slate-500 hover:text-slate-900 hover:underline ml-2"
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
                  className="text-sm"
                />
                {hasDefault && (
                  <button
                    type="button"
                    onClick={() => {
                      setUseDefault(true);
                      setOverrideFile(null);
                    }}
                    className="block mt-1 text-sm text-slate-500 hover:text-slate-900 hover:underline"
                  >
                    Use my uploaded resume instead
                  </button>
                )}
                {!hasDefault && (
                  <p className="mt-1 text-xs text-slate-400">
                    Tip: add a resume to your profile once and it'll be used by default on future
                    applications.
                  </p>
                )}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Cover letter (optional)
            </label>
            <textarea
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              rows={5}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-slate-400"
              placeholder="Why are you a good fit for this role?"
            />
          </div>

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || defaultResumeUrl === undefined}
              className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm font-medium hover:bg-slate-800 disabled:opacity-50"
            >
              {submitting ? "Submitting…" : "Submit application"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
