import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import ScheduleInterviewModal from "../../components/ScheduleInterviewModal";
import { applicationsService } from "../../services/applications";
import { timeAgo } from "../../utils/format";

// Statuses an employer may move an application TO, mirroring
// Application.EMPLOYER_ALLOWED_STATUSES on the backend. WITHDRAWN is
// deliberately absent -- that's the applicant's action alone.
const STATUS_OPTIONS = ["under_review", "shortlisted", "interview", "selected", "rejected"];

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
  const [schedulingFor, setSchedulingFor] = useState(null);
  // Which applicants have their full profile (education/experience/bio)
  // expanded. A Set, not a single id, so an employer can compare two
  // candidates' full histories side by side without one collapsing the
  // other -- and it defaults to all-collapsed so a long applicant list
  // stays scannable rather than dumping every candidate's full history at
  // once.
  const [expanded, setExpanded] = useState(() => new Set());

  const load = () =>
    applicationsService
      .applicantsForJob(jobId)
      .then(setApplications)
      .catch(() => setError("Could not load applicants for this job."));

  useEffect(() => {
    load();
  }, [jobId]);

  const changeStatus = async (appId, newStatus) => {
    try {
      await applicationsService.setStatus(appId, newStatus);
      load();
    } catch (err) {
      alert(err.response?.data?.status?.[0] || err.response?.data?.detail || "Could not update status.");
    }
  };

  const toggleExpanded = (appId) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(appId)) next.delete(appId);
      else next.add(appId);
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-3xl mx-auto px-6 py-8">
        <Link to="/employer" className="text-sm text-slate-500 hover:underline">
          &larr; Back to dashboard
        </Link>
        <div className="flex items-center justify-between">
          <h1 className="mt-2 text-xl font-semibold text-slate-900">Applicants</h1>
          <Link
            to={`/employer/jobs/${jobId}/edit`}
            className="text-sm text-slate-600 hover:underline"
          >
            Edit job
          </Link>
        </div>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        {applications === null && !error && <p className="mt-4 text-sm text-slate-400">Loading…</p>}
        {applications?.length === 0 && (
          <p className="mt-4 text-sm text-slate-400">No applications yet for this job.</p>
        )}

        <div className="mt-4 space-y-3">
          {applications?.map((app) => {
            const a = app.applicant;
            const isExpanded = expanded.has(app.id);
            const links = [
              a.github_url && { label: "GitHub", url: a.github_url },
              a.linkedin_url && { label: "LinkedIn", url: a.linkedin_url },
              a.portfolio_url && { label: "Portfolio", url: a.portfolio_url },
            ].filter(Boolean);

            return (
              <div key={app.id} className="bg-white border border-slate-200 rounded-xl p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0">
                    {a.profile_photo ? (
                      <img
                        src={a.profile_photo}
                        alt=""
                        className="h-11 w-11 rounded-full object-cover border border-slate-100 shrink-0"
                      />
                    ) : (
                      <div className="h-11 w-11 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 text-sm font-semibold shrink-0">
                        {(a.full_name || a.email)[0]?.toUpperCase()}
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="font-medium text-slate-900">{a.full_name || a.email}</p>
                      <p className="text-sm text-slate-500">{a.email}</p>
                      {a.headline && <p className="text-sm text-slate-500 mt-0.5">{a.headline}</p>}
                      {(a.location || a.phone) && (
                        <p className="text-xs text-slate-400 mt-0.5">
                          {[a.location, a.phone].filter(Boolean).join(" · ")}
                        </p>
                      )}
                    </div>
                  </div>
                  <span className="shrink-0 text-xs text-slate-400">{timeAgo(app.applied_at)}</span>
                </div>

                {links.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-3">
                    {links.map((l) => (
                      <a
                        key={l.label}
                        href={l.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-slate-500 hover:text-slate-900 hover:underline"
                      >
                        {l.label}
                      </a>
                    ))}
                  </div>
                )}

                {a.skills?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {a.skills.map((skill) => (
                      <span key={skill} className="text-xs text-slate-500 bg-slate-50 rounded px-2 py-0.5">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}

                {app.cover_letter && (
                  <p className="mt-3 text-sm text-slate-600 whitespace-pre-line">{app.cover_letter}</p>
                )}

                <button
                  onClick={() => toggleExpanded(app.id)}
                  className="mt-3 text-sm text-slate-600 hover:text-slate-900 hover:underline"
                >
                  {isExpanded ? "Hide full profile" : "View full profile"}
                </button>

                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-100 space-y-3">
                    {a.bio && (
                      <div>
                        <p className="text-xs font-semibold text-slate-700 mb-1">About</p>
                        <p className="text-sm text-slate-600 whitespace-pre-line">{a.bio}</p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <p className="text-slate-500">
                        <span className="text-slate-400">Experience:</span>{" "}
                        {a.years_of_experience} yr{a.years_of_experience === 1 ? "" : "s"}
                      </p>
                      {a.expected_salary && (
                        <p className="text-slate-500">
                          <span className="text-slate-400">Expected salary:</span>{" "}
                          ₹{(a.expected_salary / 100000).toFixed(1)}L
                        </p>
                      )}
                    </div>

                    {a.education?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-slate-700 mb-1">Education</p>
                        <div className="space-y-1.5">
                          {a.education.map((edu) => (
                            <div key={edu.id} className="text-sm">
                              <p className="text-slate-700">
                                {edu.degree}
                                {edu.field_of_study && ` in ${edu.field_of_study}`} · {edu.institution}
                              </p>
                              <p className="text-xs text-slate-400">
                                {edu.start_date} — {edu.end_date || "Present"}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {a.experience?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-slate-700 mb-1">Experience</p>
                        <div className="space-y-1.5">
                          {a.experience.map((exp) => (
                            <div key={exp.id} className="text-sm">
                              <p className="text-slate-700">
                                {exp.title} · {exp.company_name}
                              </p>
                              <p className="text-xs text-slate-400">
                                {exp.start_date} — {exp.is_current ? "Present" : exp.end_date}
                              </p>
                              {exp.description && (
                                <p className="text-sm text-slate-500 mt-0.5">{exp.description}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {a.education?.length === 0 && a.experience?.length === 0 && !a.bio && (
                      <p className="text-sm text-slate-400">
                        This candidate hasn't filled in education or experience yet.
                      </p>
                    )}
                  </div>
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

                  {app.status !== "withdrawn" && (
                    <button
                      onClick={() => setSchedulingFor(app.id)}
                      className="text-sm text-slate-600 hover:text-slate-900 hover:underline"
                    >
                      Schedule interview
                    </button>
                  )}

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
            );
          })}
        </div>
      </main>

      {schedulingFor && (
        <ScheduleInterviewModal
          applicationId={schedulingFor}
          onClose={() => setSchedulingFor(null)}
          onScheduled={() => {
            setSchedulingFor(null);
            load();
          }}
        />
      )}
    </div>
  );
}
