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
        <div className="card p-6 md:p-8">
          <div className="skeleton h-6 w-2/3 mb-3" />
          <div className="skeleton h-4 w-1/3 mb-6" />
          <div className="flex gap-2 mb-6">
            <div className="skeleton h-6 w-20 rounded-full" />
            <div className="skeleton h-6 w-24 rounded-full" />
            <div className="skeleton h-6 w-16 rounded-full" />
          </div>
          <div className="skeleton h-4 w-full mb-2" />
          <div className="skeleton h-4 w-5/6 mb-2" />
          <div className="skeleton h-4 w-2/3" />
        </div>
      </Shell>
    );
  }

  if (status === "not_found") {
    return (
      <Shell>
        <div className="card text-center py-16 px-6 animate-fade-in">
          <p className="text-ink-500">
            This job doesn't exist or is no longer available.
          </p>
          <button
            onClick={() => navigate("/")}
            className="mt-3 text-sm text-violet-700 font-semibold hover:text-violet-800"
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
        <div className="card px-6 py-8">
          <p className="text-sm text-red-600">Could not load this job. Please try again.</p>
        </div>
      </Shell>
    );
  }

  const salary = formatSalary(job.salary_min, job.salary_max);

  return (
    <Shell>
      <div className="card p-6 md:p-8 animate-fade-up">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl font-extrabold text-ink-950">{job.title}</h1>
            <Link
              to={`/companies/${job.company_slug}`}
              className="mt-1.5 inline-block text-sm text-ink-500 hover:text-violet-700 transition-colors"
            >
              {job.company_name}
            </Link>
          </div>
          <span className="shrink-0 text-xs text-ink-500/70">{timeAgo(job.published_at)}</span>
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5">
          <Tag>{job.location}</Tag>
          <Tag>{formatWorkMode(job.work_mode)}</Tag>
          <Tag>{formatEmploymentType(job.employment_type)}</Tag>
          {salary && <Tag>{salary}</Tag>}
          {job.experience_required > 0 && <Tag>{job.experience_required}+ yrs experience</Tag>}
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          {!isAuthenticated && (
            <Link to="/login" className="btn btn-primary">
              Sign in to apply
            </Link>
          )}
          {isAuthenticated && isJobSeeker && (
            <>
              {applied ? (
                <span className="badge-green badge !text-sm !py-2 !px-4">Applied ✓</span>
              ) : (
                <button
                  onClick={() => setShowApplyModal(true)}
                  disabled={!job.is_open}
                  title={!job.is_open ? "This job is no longer accepting applications" : undefined}
                  className="btn btn-primary"
                >
                  Apply
                </button>
              )}
              <button
                onClick={toggleSave}
                disabled={savePending}
                className={saved ? "btn !bg-violet-600 !text-white shadow-soft" : "btn btn-secondary"}
              >
                {saved ? "Saved ✓" : "Save job"}
              </button>
            </>
          )}
          {isAuthenticated && isEmployer && (
            <p className="text-sm text-ink-500 self-center">
              Signed in as an employer — switch to a job seeker account to apply.
            </p>
          )}
          {!job.is_open && (
            <p className="text-sm text-amber-600 self-center font-medium">
              This job is no longer accepting applications.
            </p>
          )}
        </div>

        <Section title="Description" text={job.description} />
        <Section title="Responsibilities" text={job.responsibilities} />
        <Section title="Qualifications" text={job.qualifications} />
        <Section title="Benefits" text={job.benefits} />

        {job.skills?.length > 0 && (
          <div className="mt-6 pt-6 border-t border-violet-50">
            <h2 className="font-display text-sm font-bold text-ink-950 mb-2">Skills</h2>
            <div className="flex flex-wrap gap-1.5">
              {job.skills.map((s) => (
                <Tag key={s.id}>{s.name}</Tag>
              ))}
            </div>
          </div>
        )}

        {job.application_deadline && (
          <p className="mt-6 text-xs text-ink-500">
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
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className="max-w-3xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}

function Section({ title, text }) {
  if (!text) return null;
  return (
    <div className="mt-6 pt-6 border-t border-violet-50">
      <h2 className="font-display text-sm font-bold text-ink-950 mb-1.5">{title}</h2>
      <p className="text-sm text-ink-700 whitespace-pre-line leading-relaxed">{text}</p>
    </div>
  );
}

function Tag({ children }) {
  return <span className="badge badge-neutral">{children}</span>;
}
