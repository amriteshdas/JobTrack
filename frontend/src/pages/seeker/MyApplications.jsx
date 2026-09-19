import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import { applicationsService } from "../../services/applications";
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

  const load = () => applicationsService.mine().then(setApplications);
  useEffect(load, []);

  const withdraw = async (id) => {
    if (!window.confirm("Withdraw this application? This can't be undone.")) return;
    await applicationsService.withdraw(id);
    load();
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-xl font-semibold text-slate-900 mb-6">Your applications</h1>

        {applications === null && <p className="text-sm text-slate-400">Loading…</p>}

        {applications?.length === 0 && (
          <p className="text-sm text-slate-400">
            You haven't applied to anything yet. Browse the marketplace to get started.
          </p>
        )}

        <div className="space-y-3">
          {applications?.map((app) => (
            <div key={app.id} className="bg-white border border-slate-200 rounded-xl p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <Link
                    to={`/jobs/${app.job.id}`}
                    className="font-medium text-slate-900 hover:underline"
                  >
                    {app.job.title}
                  </Link>
                  <p className="text-sm text-slate-500">{app.job.company_name}</p>
                </div>
                <span
                  className={`shrink-0 text-xs font-medium rounded-full px-2.5 py-1 ${STATUS_STYLES[app.status]}`}
                >
                  {STATUS_LABELS[app.status]}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-400">Applied {timeAgo(app.applied_at)}</p>

              {!["withdrawn", "rejected", "selected"].includes(app.status) && (
                <button
                  onClick={() => withdraw(app.id)}
                  className="mt-2 text-xs text-slate-400 hover:text-red-600"
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
