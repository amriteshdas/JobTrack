import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Navbar from "../../components/Navbar";
import ApplyModal from "../../components/ApplyModal";
import { formatEmploymentType, formatSalary, formatWorkMode, timeAgo } from "../../utils/format";
import { jobsService } from "../../services/jobs";
import { savedJobsService } from "../../services/profile";
import { applicationsService } from "../../services/applications";
import { useAuth } from "../../context/AuthContext";

/**
 * Apply is now real, as of Phase 6 -- it opens ApplyModal, which submits a
 * resume + optional cover letter to POST /jobs/{id}/apply/. Save/unsave has
 * been real since Phase 5.
 */
export default function JobDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, isJobSeeker, isEmployer } = useAuth();

  const [job, setJob] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ok | not_found | error
  const [saved, setSaved] = useState(false);
  const [savePending, setSavePending] = useState(false);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [applied, setApplied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");

    jobsService
      .get(id)
      .then((data) => {
        if (!cancelled) {
          setJob(data);
          setStatus("ok");
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setStatus(err.response?.status === 404 ? "not_found" : "error");
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  // Separate effect: only fetch the saved-jobs list once we know both who
  // the user is AND which job we're looking at. Bundling this into the job
  // effect above would refire the saved-list request every time the job
  // itself reloads, which is unnecessary.
  useEffect(() => {
    if (!isAuthenticated || !isJobSeeker) return;
    let cancelled = false;
    savedJobsService
      .list()
      .then((entries) => {
        if (!cancelled) setSaved(entries.some((e) => String(e.job.id) === String(id)));
      })
      .catch(() => {
        /* Non-fatal: the Save button just falls back to its default
           (not-saved) state if this lookup fails. */
      });
    return () => {
      cancelled = true;
    };
  }, [id, isAuthenticated, isJobSeeker]);

  // Separate effect, same reasoning as the saved-status one above: only
  // fires once we know who the user is, and doesn't refire when the job
  // itself reloads.
  useEffect(() => {
    if (!isAuthenticated || !isJobSeeker) return;
    let cancelled = false;
    applicationsService
      .mine()
      .then((apps) => {
        if (!cancelled) setApplied(apps.some((a) => String(a.job.id) === String(id) && a.status !== "withdrawn"));
      })
      .catch(() => {
        /* Non-fatal: the Apply button just falls back to its default
           (not-applied) state if this lookup fails. */
      });
    return () => {
      cancelled = true;
    };
  }, [id, isAuthenticated, isJobSeeker]);

  const toggleSave = async () => {
    setSavePending(true);
    try {
      if (saved) {
        await savedJobsService.unsave(id);
        setSaved(false);
      } else {
        await savedJobsService.save(id);
        setSaved(true);
      }
    } finally {
      setSavePending(false);
    }
  };

  if (status === "loading") {
    return (
      <Shell>
        <p className="text-sm text-slate-400">Loading…</p>
      </Shell>
    );
  }

  if (status === "not_found") {
    return (
      <Shell>
        <div className="text-center py-16">
          <p className="text-slate-500">
            This job doesn't exist or is no longer available.
          </p>
          <button
            onClick={() => navigate("/")}
            className="mt-3 text-sm text-slate-900 font-medium hover:underline"
          >
            Back to job search
          </button>
        </div>
      </Shell>
    );
  }

  if (status === "error") {
    return (
      <Shell>
        <p className="text-sm text-red-600">Could not load this job. Please try again.</p>
      </Shell>
    );
  }

  const salary = formatSalary(job.salary_min, job.salary_max);

  return (
    <Shell>
      <div className="bg-white border border-slate-200 rounded-2xl p-6 md:p-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">{job.title}</h1>
            <Link
              to={`/companies/${job.company_slug}`}
              className="mt-1 inline-block text-sm text-slate-500 hover:text-slate-900 hover:underline"
            >
              {job.company_name}
            </Link>
          </div>
          <span className="shrink-0 text-xs text-slate-400">{timeAgo(job.published_at)}</span>
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5">
          <Tag>{job.location}</Tag>
          <Tag>{formatWorkMode(job.work_mode)}</Tag>
          <Tag>{formatEmploymentType(job.employment_type)}</Tag>
          {salary && <Tag>{salary}</Tag>}
          {job.experience_required > 0 && <Tag>{job.experience_required}+ yrs experience</Tag>}
        </div>

        <div className="mt-6 flex gap-3">
          {!isAuthenticated && (
            <Link
              to="/login"
              className="rounded-lg bg-slate-900 text-white px-5 py-2.5 text-sm font-medium hover:bg-slate-800"
            >
              Sign in to apply
            </Link>
          )}
          {isAuthenticated && isJobSeeker && (
            <>
              {applied ? (
                <span className="rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 px-5 py-2.5 text-sm font-medium">
                  Applied ✓
                </span>
              ) : (
                <button
                  onClick={() => setShowApplyModal(true)}
                  disabled={!job.is_open}
                  title={!job.is_open ? "This job is no longer accepting applications" : undefined}
                  className="rounded-lg bg-slate-900 text-white px-5 py-2.5 text-sm font-medium hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Apply
                </button>
              )}
              <button
                onClick={toggleSave}
                disabled={savePending}
                className={`rounded-lg border px-5 py-2.5 text-sm font-medium transition disabled:opacity-50 ${
                  saved
                    ? "border-slate-900 bg-slate-900 text-white hover:bg-slate-800"
                    : "border-slate-300 text-slate-700 hover:bg-slate-50"
                }`}
              >
                {saved ? "Saved ✓" : "Save job"}
              </button>
            </>
          )}
          {isAuthenticated && isEmployer && (
            <p className="text-sm text-slate-400 self-center">
              Signed in as an employer — switch to a job seeker account to apply.
            </p>
          )}
          {!job.is_open && (
            <p className="text-sm text-amber-600 self-center">
              This job is no longer accepting applications.
            </p>
          )}
        </div>

        <Section title="Description" text={job.description} />
        <Section title="Responsibilities" text={job.responsibilities} />
        <Section title="Qualifications" text={job.qualifications} />
        <Section title="Benefits" text={job.benefits} />

        {job.skills?.length > 0 && (
          <div className="mt-6">
            <h2 className="text-sm font-semibold text-slate-900 mb-2">Skills</h2>
            <div className="flex flex-wrap gap-1.5">
              {job.skills.map((s) => (
                <Tag key={s.id}>{s.name}</Tag>
              ))}
            </div>
          </div>
        )}

        {job.application_deadline && (
          <p className="mt-6 text-xs text-slate-400">
            Applications close {new Date(job.application_deadline).toLocaleDateString()}.
          </p>
        )}
      </div>

      {showApplyModal && (
        <ApplyModal
          jobId={id}
          onClose={() => setShowApplyModal(false)}
          onApplied={() => {
            setShowApplyModal(false);
            setApplied(true);
          }}
        />
      )}
    </Shell>
  );
}

function Shell({ children }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-3xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}

function Section({ title, text }) {
  if (!text) return null;
  return (
    <div className="mt-6">
      <h2 className="text-sm font-semibold text-slate-900 mb-1.5">{title}</h2>
      <p className="text-sm text-slate-600 whitespace-pre-line leading-relaxed">{text}</p>
    </div>
  );
}

function Tag({ children }) {
  return (
    <span className="text-xs font-medium text-slate-600 bg-slate-100 rounded-full px-2.5 py-1">
      {children}
    </span>
  );
}
