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
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="font-display text-xl font-extrabold text-ink-950 mb-6 animate-fade-up">Saved jobs</h1>

        {saved === null && (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="card p-5 h-[104px]">
                <div className="skeleton h-4 w-1/3 mb-3" />
                <div className="skeleton h-3 w-1/2" />
              </div>
            ))}
          </div>
        )}

        {saved?.length === 0 && (
          <div className="card text-center py-14 px-6 animate-fade-in">
            <p className="text-sm text-ink-500">
              You haven't saved any jobs yet. Browse the marketplace and tap "Save job" on
              anything that catches your eye.
            </p>
          </div>
        )}

        <div className="space-y-3">
          {saved?.map((entry, i) => (
            <div key={entry.id} className="relative">
              <JobCard job={entry.job} index={i} />
              <button
                onClick={() => unsave(entry.job.id)}
                className="absolute top-4 right-4 text-xs font-medium text-ink-500 hover:text-red-600 bg-white/90 rounded-md px-2 py-1 transition-colors"
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
