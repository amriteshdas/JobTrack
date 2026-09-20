import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import JobCard from "../../components/JobCard";
import { savedJobsService } from "../../services/profile";

export default function SavedJobs() {
  const [saved, setSaved] = useState(null);

  const load = () => savedJobsService.list().then(setSaved).catch(() => setSaved([]));
  useEffect(() => {
    load();
  }, []);

  const unsave = async (jobId) => {
    await savedJobsService.unsave(jobId);
    load();
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-xl font-semibold text-slate-900 mb-6">Saved jobs</h1>

        {saved === null && <p className="text-sm text-slate-400">Loading…</p>}

        {saved?.length === 0 && (
          <p className="text-sm text-slate-400">
            You haven't saved any jobs yet. Browse the marketplace and tap "Save job" on
            anything that catches your eye.
          </p>
        )}

        <div className="space-y-3">
          {saved?.map((entry) => (
            <div key={entry.id} className="relative">
              <JobCard job={entry.job} />
              <button
                onClick={() => unsave(entry.job.id)}
                className="absolute top-4 right-4 text-xs text-slate-400 hover:text-red-600 bg-white"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
