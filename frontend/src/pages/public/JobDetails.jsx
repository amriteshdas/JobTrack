import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Navbar from "../../components/Navbar";
import { formatEmploymentType, formatSalary, formatWorkMode, timeAgo } from "../../utils/format";
import { jobsService } from "../../services/jobs";
import { useAuth } from "../../context/AuthContext";

/**
 * Apply / Save actions are rendered but disabled with a note -- the
 * Application model doesn't exist until Phase 6, and Saved Jobs is Phase 5.
 * Showing the buttons now (rather than omitting them) is deliberate: it
 * keeps the page layout stable across phases instead of components
 * appearing and shifting things around later.
 */
export default function JobDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, isJobSeeker, isEmployer } = useAuth();

  const [job, setJob] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ok | not_found | error

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
              <button
                disabled
                title="Applications are implemented in Phase 6"
                className="rounded-lg bg-slate-900 text-white px-5 py-2.5 text-sm font-medium opacity-50 cursor-not-allowed"
              >
                Apply
              </button>
              <button
                disabled
                title="Saved jobs are implemented in Phase 5"
                className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium opacity-50 cursor-not-allowed"
              >
                Save job
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
