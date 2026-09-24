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
    <div className="min-h-screen bg-violet-50/60">
      <Navbar />
      <main className="max-w-3xl mx-auto px-6 py-8">
        <Link to="/employer" className="text-sm font-medium text-ink-500 hover:text-violet-700 transition-colors">
          &larr; Back to dashboard
        </Link>
        <div className="flex items-center justify-between">
          <h1 className="font-display mt-2 text-xl font-extrabold text-ink-950">Applicants</h1>
          <Link
            to={`/employer/jobs/${jobId}/edit`}
            className="text-sm font-medium text-violet-600 hover:text-violet-800 transition-colors"
          >
            Edit job
          </Link>
        </div>

        {error && (
          <div className="mt-4 card px-4 py-3">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
        {applications === null && !error && (
          <div className="mt-4 space-y-3">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="card p-4 h-24">
                <div className="skeleton h-4 w-1/3 mb-2" />
                <div className="skeleton h-3 w-1/2" />
              </div>
            ))}
          </div>
        )}
        {applications?.length === 0 && (
          <div className="mt-4 card text-center py-14 px-6 animate-fade-in">
            <p className="text-sm text-ink-500">No applications yet for this job.</p>
          </div>
        )}

        <div className="mt-4 space-y-3">
          {applications?.map((app, idx) => {
            const a = app.applicant;
            const isExpanded = expanded.has(app.id);
            const links = [
              a.github_url && { label: "GitHub", url: a.github_url },
              a.linkedin_url && { label: "LinkedIn", url: a.linkedin_url },
              a.portfolio_url && { label: "Portfolio", url: a.portfolio_url },
            ].filter(Boolean);

            return (
              <div key={app.id} style={{ "--reveal-index": idx }} className="reveal card p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0">
                    {a.profile_photo ? (
                      <img
                        src={a.profile_photo}
                        alt=""
                        className="h-11 w-11 rounded-full object-cover border border-violet-100 shrink-0"
                      />
                    ) : (
                      <div className="h-11 w-11 rounded-full bg-gradient-to-br from-violet-100 to-sky-100 flex items-center justify-center text-violet-600 text-sm font-display font-bold shrink-0">
                        {(a.full_name || a.email)[0]?.toUpperCase()}
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="font-medium text-ink-950">{a.full_name || a.email}</p>
                      <p className="text-sm text-ink-500">{a.email}</p>
                      {a.headline && <p className="text-sm text-ink-500 mt-0.5">{a.headline}</p>}
                      {(a.location || a.phone) && (
                        <p className="text-xs text-ink-500 mt-0.5">
                          {[a.location, a.phone].filter(Boolean).join(" · ")}
                        </p>
                      )}
                    </div>
                  </div>
                  <span className="shrink-0 text-xs text-ink-500">{timeAgo(app.applied_at)}</span>
                </div>

                {links.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-3">
                    {links.map((l) => (
                      <a
                        key={l.label}
                        href={l.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-ink-500 hover:text-ink-950 hover:underline"
                      >
                        {l.label}
                      </a>
                    ))}
                  </div>
                )}

                {a.skills?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {a.skills.map((skill) => (
                      <span key={skill} className="text-xs text-ink-500 bg-violet-50/60 rounded-md px-2 py-0.5">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}

                {app.cover_letter && (
                  <p className="mt-3 text-sm text-ink-700 whitespace-pre-line">{app.cover_letter}</p>
                )}

                <button
                  onClick={() => toggleExpanded(app.id)}
                  className="mt-3 text-sm text-ink-700 hover:text-ink-950 hover:underline"
                >
                  {isExpanded ? "Hide full profile" : "View full profile"}
                </button>

                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-violet-50 space-y-3">
                    {a.bio && (
                      <div>
                        <p className="text-xs font-semibold text-ink-700 mb-1">About</p>
                        <p className="text-sm text-ink-700 whitespace-pre-line">{a.bio}</p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <p className="text-ink-500">
                        <span className="text-ink-500">Experience:</span>{" "}
                        {a.years_of_experience} yr{a.years_of_experience === 1 ? "" : "s"}
                      </p>
                      {a.expected_salary && (
                        <p className="text-ink-500">
                          <span className="text-ink-500">Expected salary:</span>{" "}
                          ₹{(a.expected_salary / 100000).toFixed(1)}L
                        </p>
                      )}
                    </div>

                    {a.education?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-ink-700 mb-1">Education</p>
                        <div className="space-y-1.5">
                          {a.education.map((edu) => (
                            <div key={edu.id} className="text-sm">
                              <p className="text-ink-700">
                                {edu.degree}
                                {edu.field_of_study && ` in ${edu.field_of_study}`} · {edu.institution}
                              </p>
                              <p className="text-xs text-ink-500">
                                {edu.start_date} — {edu.end_date || "Present"}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {a.experience?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-ink-700 mb-1">Experience</p>
                        <div className="space-y-1.5">
                          {a.experience.map((exp) => (
                            <div key={exp.id} className="text-sm">
                              <p className="text-ink-700">
                                {exp.title} · {exp.company_name}
                              </p>
                              <p className="text-xs text-ink-500">
                                {exp.start_date} — {exp.is_current ? "Present" : exp.end_date}
                              </p>
                              {exp.description && (
                                <p className="text-sm text-ink-500 mt-0.5">{exp.description}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {a.education?.length === 0 && a.experience?.length === 0 && !a.bio && (
                      <p className="text-sm text-ink-500">
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
                    className="text-sm text-ink-950 font-medium hover:underline"
                  >
                    View resume
                  </a>

                  {app.status !== "withdrawn" && (
                    <button
                      onClick={() => setSchedulingFor(app.id)}
                      className="text-sm text-ink-700 hover:text-ink-950 hover:underline"
                    >
                      Schedule interview
                    </button>
                  )}

                  {app.status === "withdrawn" ? (
                    <span className="text-xs text-ink-500 ml-auto">Withdrawn by candidate</span>
                  ) : (
                    <select
                      value={app.status}
                      onChange={(e) => changeStatus(app.id, e.target.value)}
                      className="ml-auto text-sm border border-violet-100 rounded-lg px-2 py-1.5 focus:outline-none"
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
