import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import StatCard from "../../components/StatCard";
import JobCard from "../../components/JobCard";
import { useAuth } from "../../context/AuthContext";
import { dashboardService } from "../../services/dashboard";
import { timeAgo } from "../../utils/format";

const STATUS_STYLES = {
  applied: "bg-slate-100 text-slate-700",
  under_review: "bg-blue-50 text-blue-700",
  shortlisted: "bg-amber-50 text-amber-700",
  interview: "bg-purple-50 text-purple-700",
  selected: "bg-emerald-50 text-emerald-700",
  rejected: "bg-red-50 text-red-700",
  withdrawn: "bg-slate-100 text-slate-400",
};

export default function SeekerDashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    dashboardService
      .seeker()
      .then(setData)
      .catch(() => setError("Could not load your dashboard. Please try refreshing."));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Job Seeker</p>
            <h1 className="text-xl font-semibold text-slate-900">
              Welcome, {user.full_name || user.email}
            </h1>
          </div>
          <div className="flex gap-2">
            <Link to="/seeker/profile" className="text-sm text-slate-600 hover:underline">
              Edit profile
            </Link>
            <span className="text-slate-300">·</span>
            <Link to="/seeker/saved-jobs" className="text-sm text-slate-600 hover:underline">
              Saved jobs
            </Link>
            <span className="text-slate-300">·</span>
            <Link to="/seeker/applications" className="text-sm text-slate-600 hover:underline">
              All applications
            </Link>
          </div>
        </div>

        {error ? (
          <p className="text-sm text-red-600">{error}</p>
        ) : !data ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <StatCard label="Total applications" value={data.stats.total_applications} />
              <StatCard label="Under review" value={data.stats.under_review} />
              <StatCard label="Shortlisted" value={data.stats.shortlisted} />
              <StatCard label="Interviews" value={data.stats.interview} />
              <StatCard label="Saved jobs" value={data.stats.saved_jobs} />
            </div>

            <div className="grid md:grid-cols-2 gap-6 mt-8">
              <section>
                <h2 className="text-sm font-semibold text-slate-900 mb-3">Recent applications</h2>
                {data.recent_applications.length === 0 ? (
                  <p className="text-sm text-slate-400">No applications yet.</p>
                ) : (
                  <div className="space-y-2">
                    {data.recent_applications.map((app) => (
                      <Link
                        key={app.id}
                        to={`/jobs/${app.job_id}`}
                        className="flex items-center justify-between bg-white border border-slate-200 rounded-lg px-3 py-2.5 hover:border-slate-300"
                      >
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-900 truncate">
                            {app.job_title}
                          </p>
                          <p className="text-xs text-slate-400">
                            {app.company_name} · {timeAgo(app.applied_at)}
                          </p>
                        </div>
                        <span
                          className={`shrink-0 text-xs font-medium rounded-full px-2 py-0.5 ml-2 ${STATUS_STYLES[app.status]}`}
                        >
                          {app.status.replace("_", " ")}
                        </span>
                      </Link>
                    ))}
                  </div>
                )}

                <h2 className="text-sm font-semibold text-slate-900 mb-3 mt-6">
                  Upcoming interviews
                </h2>
                {data.upcoming_interviews.length === 0 ? (
                  <p className="text-sm text-slate-400">No interviews scheduled right now.</p>
                ) : (
                  <div className="space-y-2">
                    {data.upcoming_interviews.map((iv) => (
                      <div
                        key={iv.id}
                        className="bg-white border border-slate-200 rounded-lg px-3 py-2.5"
                      >
                        <p className="text-sm font-medium text-slate-900">{iv.job_title}</p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {iv.company_name} · {new Date(iv.scheduled_at).toLocaleString()}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5 capitalize">
                          {iv.interview_type}
                          {iv.meeting_link && (
                            <>
                              {" · "}
                              <a
                                href={iv.meeting_link}
                                target="_blank"
                                rel="noreferrer"
                                className="text-slate-600 hover:underline"
                              >
                                Join link
                              </a>
                            </>
                          )}
                          {iv.location && ` · ${iv.location}`}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section>
                <h2 className="text-sm font-semibold text-slate-900 mb-3">Recommended for you</h2>
                {data.recommended_jobs.length === 0 ? (
                  <p className="text-sm text-slate-400">No recommendations yet.</p>
                ) : (
                  <div className="space-y-2">
                    {data.recommended_jobs.map((job) => (
                      <JobCard key={job.id} job={job} />
                    ))}
                  </div>
                )}
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
