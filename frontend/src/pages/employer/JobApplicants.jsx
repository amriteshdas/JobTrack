import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import { applicationsService } from "../../services/applications";
import { timeAgo } from "../../utils/format";

// Statuses an employer may move an application TO, mirroring
// Application.EMPLOYER_ALLOWED_STATUSES on the backend. WITHDRAWN is
// deliberately absent -- that's the applicant's action alone.
const STATUS_OPTIONS = [
  "under_review",
  "shortlisted",
  "interview",
  "selected",
  "rejected",
];

const STATUS_LABELS = {
  applied: "Applied",
  under_review: "Under review",
  shortlisted: "Shortlisted",
  interview: "Interview",
  selected: "Selected",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

export default function JobApplicants() {
  const { jobId } = useParams();
  const [applications, setApplications] = useState(null);
  const [error, setError] = useState(null);

  const load = () =>
    applicationsService
      .applicantsForJob(jobId)
      .then(setApplications)
      .catch(() => setError("Could not load applicants for this job."));

  useEffect(load, [jobId]);

  const changeStatus = async (appId, newStatus) => {
    try {
      await applicationsService.setStatus(appId, newStatus);
      load();
    } catch (err) {
      alert(err.response?.data?.status?.[0] || err.response?.data?.detail || "Could not update status.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-3xl mx-auto px-6 py-8">
        <Link to="/employer" className="text-sm text-slate-500 hover:underline">
          &larr; Back to dashboard
        </Link>
        <h1 className="mt-2 text-xl font-semibold text-slate-900">Applicants</h1>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        {applications === null && !error && <p className="mt-4 text-sm text-slate-400">Loading…</p>}
        {applications?.length === 0 && (
          <p className="mt-4 text-sm text-slate-400">No applications yet for this job.</p>
        )}

        <div className="mt-4 space-y-3">
          {applications?.map((app) => (
            <div key={app.id} className="bg-white border border-slate-200 rounded-xl p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="font-medium text-slate-900">
                    {app.applicant.full_name || app.applicant.email}
                  </p>
                  <p className="text-sm text-slate-500">{app.applicant.email}</p>
                  {app.applicant.headline && (
                    <p className="text-sm text-slate-500 mt-0.5">{app.applicant.headline}</p>
                  )}
                </div>
                <span className="shrink-0 text-xs text-slate-400">{timeAgo(app.applied_at)}</span>
              </div>

              {app.applicant.skills?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {app.applicant.skills.map((skill) => (
                    <span key={skill} className="text-xs text-slate-500 bg-slate-50 rounded px-2 py-0.5">
                      {skill}
                    </span>
                  ))}
                </div>
              )}

              {app.cover_letter && (
                <p className="mt-3 text-sm text-slate-600 whitespace-pre-line">{app.cover_letter}</p>
              )}

              <div className="mt-3 flex items-center gap-3">
                <a
                  href={app.resume}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-slate-900 font-medium hover:underline"
                >
                  View resume
                </a>

                {app.status === "withdrawn" ? (
                  <span className="text-xs text-slate-400 ml-auto">Withdrawn by candidate</span>
                ) : (
                  <select
                    value={app.status}
                    onChange={(e) => changeStatus(app.id, e.target.value)}
                    className="ml-auto text-sm border border-slate-300 rounded-lg px-2 py-1.5 focus:outline-none"
                  >
                    <option value={app.status} disabled hidden>
                      {STATUS_LABELS[app.status]}
                    </option>
                    {STATUS_OPTIONS.filter((s) => s !== app.status).map((s) => (
                      <option key={s} value={s}>
                        Move to: {STATUS_LABELS[s]}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
