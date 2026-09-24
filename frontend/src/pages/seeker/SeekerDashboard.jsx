import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import StatCard from "../../components/StatCard";
import JobCard from "../../components/JobCard";
import { useAuth } from "../../context/AuthContext";
import { dashboardService } from "../../services/dashboard";
import { timeAgo } from "../../utils/format";

const STATUS_STYLES = {
  applied: "badge-neutral",
  under_review: "badge-sky",
  shortlisted: "badge-amber",
  interview: "badge",
  selected: "badge-green",
  rejected: "badge-red",
  withdrawn: "badge-neutral opacity-60",
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
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6 animate-fade-up">
          <div>
            <p className="text-xs font-semibold text-violet-600">Job Seeker</p>
            <h1 className="font-display text-xl font-extrabold text-ink-950 mt-0.5">
              Welcome, {user.full_name || user.email}
            </h1>
          </div>
          <div className="flex gap-4">
            <Link to="/seeker/profile" className="text-sm font-medium text-ink-700 hover:text-violet-700 transition-colors">
              Edit profile
            </Link>
            <Link to="/seeker/saved-jobs" className="text-sm font-medium text-ink-700 hover:text-violet-700 transition-colors">
              Saved jobs
            </Link>
            <Link to="/seeker/applications" className="text-sm font-medium text-ink-700 hover:text-violet-700 transition-colors">
              All applications
            </Link>
          </div>
        </div>

        {error ? (
          <div className="card px-6 py-8">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        ) : !data ? (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="card p-4 h-20">
                <div className="skeleton h-6 w-10 mb-2" />
                <div className="skeleton h-3 w-16" />
              </div>
            ))}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <StatCard label="Total applications" value={data.stats.total_applications} index={0} />
              <StatCard label="Under review" value={data.stats.under_review} index={1} />
              <StatCard label="Shortlisted" value={data.stats.shortlisted} index={2} />
              <StatCard label="Interviews" value={data.stats.interview} index={3} />
              <StatCard label="Saved jobs" value={data.stats.saved_jobs} index={4} />
            </div>

            <div className="grid md:grid-cols-2 gap-6 mt-8">
              <section>
                <h2 className="font-display text-sm font-bold text-ink-950 mb-3">Recent applications</h2>
                {data.recent_applications.length === 0 ? (
                  <p className="text-sm text-ink-500">No applications yet.</p>
                ) : (
                  <div className="space-y-2">
                    {data.recent_applications.map((app) => (
                      <Link
                        key={app.id}
                        to={`/jobs/${app.job_id}`}
                        className="card card-hover flex items-center justify-between px-3.5 py-2.5"
                      >
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-ink-950 truncate">
                            {app.job_title}
                          </p>
                          <p className="text-xs text-ink-500">
                            {app.company_name} · {timeAgo(app.applied_at)}
                          </p>
                        </div>
                        <span className={`badge ${STATUS_STYLES[app.status]} shrink-0 ml-2 capitalize`}>
                          {app.status.replace("_", " ")}
                        </span>
                      </Link>
                    ))}
                  </div>
                )}

                <h2 className="font-display text-sm font-bold text-ink-950 mb-3 mt-6">
                  Upcoming interviews
                </h2>
                {data.upcoming_interviews.length === 0 ? (
                  <p className="text-sm text-ink-500">No interviews scheduled right now.</p>
                ) : (
                  <div className="space-y-2">
                    {data.upcoming_interviews.map((iv) => (
                      <div key={iv.id} className="card px-3.5 py-2.5">
                        <p className="text-sm font-semibold text-ink-950">{iv.job_title}</p>
                        <p className="text-xs text-ink-500 mt-0.5">
                          {iv.company_name} · {new Date(iv.scheduled_at).toLocaleString()}
                        </p>
                        <p className="text-xs text-ink-500/80 mt-0.5 capitalize">
                          {iv.interview_type}
                          {iv.meeting_link && (
                            <>
                              {" · "}
                              <a
                                href={iv.meeting_link}
                                target="_blank"
                                rel="noreferrer"
                                className="text-violet-600 font-medium hover:text-violet-800"
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
                <h2 className="font-display text-sm font-bold text-ink-950 mb-3">Recommended for you</h2>
                {data.recommended_jobs.length === 0 ? (
                  <p className="text-sm text-ink-500">No recommendations yet.</p>
                ) : (
                  <div className="space-y-2">
                    {data.recommended_jobs.map((job, i) => (
                      <JobCard key={job.id} job={job} index={i} />
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
