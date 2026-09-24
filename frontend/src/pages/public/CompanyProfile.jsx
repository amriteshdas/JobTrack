import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Navbar from "../../components/Navbar";
import JobCard from "../../components/JobCard";
import { companiesService } from "../../services/jobs";

export default function CompanyProfile() {
  const { slug } = useParams();

  const [company, setCompany] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");

    // Two independent requests, fired together -- the jobs list and the
    // company header are separate concerns on the backend (see the /jobs/
    // action's docstring) and there's no reason to wait for one before
    // starting the other.
    Promise.all([companiesService.get(slug), companiesService.jobs(slug)])
      .then(([companyData, jobsData]) => {
        if (cancelled) return;
        setCompany(companyData);
        setJobs(jobsData.results);
        setStatus("ok");
      })
      .catch((err) => {
        if (cancelled) return;
        setStatus(err.response?.status === 404 ? "not_found" : "error");
      });

    return () => {
      cancelled = true;
    };
  }, [slug]);

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className="max-w-4xl mx-auto px-6 py-8">
        {status === "loading" && (
          <div className="card p-6 flex items-center gap-4">
            <div className="skeleton h-16 w-16 rounded-xl shrink-0" />
            <div className="flex-1">
              <div className="skeleton h-5 w-1/3 mb-2" />
              <div className="skeleton h-3.5 w-1/2" />
            </div>
          </div>
        )}

        {status === "not_found" && (
          <div className="card text-center py-16 animate-fade-in">
            <p className="text-ink-500 text-sm">This company page doesn't exist.</p>
          </div>
        )}

        {status === "error" && (
          <div className="card px-6 py-8">
            <p className="text-sm text-red-600">Could not load this company. Please try again.</p>
          </div>
        )}

        {status === "ok" && (
          <>
            <div className="card p-6 flex items-start gap-4 animate-fade-up">
              {company.logo ? (
                <img
                  src={company.logo}
                  alt={`${company.name} logo`}
                  className="h-16 w-16 rounded-xl object-cover border border-violet-100"
                />
              ) : (
                <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-violet-100 to-sky-100 flex items-center justify-center text-violet-600 text-xl font-display font-extrabold">
                  {company.name[0]}
                </div>
              )}
              <div className="min-w-0">
                <h1 className="font-display text-xl font-extrabold text-ink-950">{company.name}</h1>
                <p className="mt-0.5 text-sm text-ink-500">
                  {[company.industry, company.location, company.company_size]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
                {company.website && (
                  <a
                    href={company.website}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 inline-block text-sm text-violet-700 hover:text-violet-800 font-medium"
                  >
                    {company.website}
                  </a>
                )}
              </div>
            </div>

            {company.description && (
              <p className="mt-4 text-sm text-ink-700 leading-relaxed whitespace-pre-line animate-fade-up">
                {company.description}
              </p>
            )}

            <h2 className="mt-8 font-display text-sm font-bold text-ink-950">
              Open roles ({company.open_jobs_count})
            </h2>
            <div className="mt-3 space-y-3">
              {jobs.length === 0 ? (
                <p className="text-sm text-ink-500">No open roles right now.</p>
              ) : (
                jobs.map((job, i) => <JobCard key={job.id} job={job} index={i} />)
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
