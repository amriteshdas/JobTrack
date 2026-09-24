import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import { applicationsService } from "../../services/applications";
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

const STATUS_LABELS = {
  applied: "Applied",
  under_review: "Under review",
  shortlisted: "Shortlisted",
  interview: "Interview",
  selected: "Selected",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

export default function MyApplications() {
  const [applications, setApplications] = useState(null);

  const load = () => applicationsService.mine().then(setApplications).catch(() => setApplications([]));
  useEffect(() => {
    load();
  }, []);

  const withdraw = async (id) => {
    if (!window.confirm("Withdraw this application? This can't be undone.")) return;
    await applicationsService.withdraw(id);
    load();
  };

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="font-display text-xl font-extrabold text-ink-950 mb-6 animate-fade-up">Your applications</h1>

        {applications === null && (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="card p-4 h-20">
                <div className="skeleton h-4 w-1/3 mb-2" />
                <div className="skeleton h-3 w-1/4" />
              </div>
            ))}
          </div>
        )}

        {applications?.length === 0 && (
          <div className="card text-center py-14 px-6 animate-fade-in">
            <p className="text-sm text-ink-500">
              You haven't applied to anything yet. Browse the marketplace to get started.
            </p>
          </div>
        )}

        <div className="space-y-3">
          {applications?.map((app, i) => (
            <div key={app.id} style={{ "--reveal-index": i }} className="reveal card p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <Link to={`/jobs/${app.job.id}`} className="font-semibold text-ink-950 hover:text-violet-700 transition-colors">
                    {app.job.title}
                  </Link>
                  <p className="text-sm text-ink-500">{app.job.company_name}</p>
                </div>
                <span className={`badge ${STATUS_STYLES[app.status]} shrink-0`}>
                  {STATUS_LABELS[app.status]}
                </span>
              </div>
              <p className="mt-2 text-xs text-ink-500/80">Applied {timeAgo(app.applied_at)}</p>

              {!["withdrawn", "rejected", "selected"].includes(app.status) && (
                <button
                  onClick={() => withdraw(app.id)}
                  className="mt-2 text-xs font-medium text-ink-500 hover:text-red-600 transition-colors"
                >
                  Withdraw application
                </button>
              )}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
