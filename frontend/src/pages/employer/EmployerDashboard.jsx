import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { jobsService } from "../../services/jobs";
import { formatEmploymentType, formatWorkMode } from "../../utils/format";

// Still a placeholder for the real analytics dashboard (Phase 7: applicant
// counts, funnel stats). What's real as of Phase 6: the job list and the
// link through to each job's applicants.
export default function EmployerDashboard() {
  const { user, logout } = useAuth();
  const [jobs, setJobs] = useState(null);

  useEffect(() => {
    jobsService.mine().then(setJobs);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-2xl mx-auto bg-white border border-slate-200 rounded-2xl p-6">
        <p className="text-xs uppercase tracking-wide text-slate-400">Employer</p>
        <h1 className="mt-1 text-xl font-semibold text-slate-900">
          Welcome, {user.full_name || user.email}
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Full analytics arrive in Phase 7. For now, your postings:
        </p>

        <div className="mt-4 space-y-2">
          {jobs === null && <p className="text-sm text-slate-400">Loading…</p>}
          {jobs?.length === 0 && (
            <p className="text-sm text-slate-400">
              No jobs posted yet. Job creation UI lands with Phase 7's dashboard build-out --
              for now, jobs can be created via the API directly.
            </p>
          )}
          {jobs?.map((job) => (
            <div
              key={job.id}
              className="flex items-center justify-between border border-slate-100 rounded-lg px-3 py-2.5"
            >
              <div>
                <p className="text-sm font-medium text-slate-900">{job.title}</p>
                <p className="text-xs text-slate-400">
                  {formatWorkMode(job.work_mode)} · {formatEmploymentType(job.employment_type)} ·{" "}
                  <span className="capitalize">{job.status}</span>
                </p>
              </div>
              <Link
                to={`/employer/jobs/${job.id}/applicants`}
                className="text-sm text-slate-900 font-medium hover:underline"
              >
                Applicants
              </Link>
            </div>
          ))}
        </div>

        <button
          onClick={logout}
          className="mt-5 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Log out
        </button>
      </div>
    </div>
  );
}
