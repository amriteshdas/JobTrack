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
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-4xl mx-auto px-6 py-8">
        {status === "loading" && <p className="text-sm text-slate-400">Loading…</p>}

        {status === "not_found" && (
          <p className="text-sm text-slate-500 text-center py-16">
            This company page doesn't exist.
          </p>
        )}

        {status === "error" && (
          <p className="text-sm text-red-600">Could not load this company. Please try again.</p>
        )}

        {status === "ok" && (
          <>
            <div className="bg-white border border-slate-200 rounded-2xl p-6 flex items-start gap-4">
              {company.logo ? (
                <img
                  src={company.logo}
                  alt={`${company.name} logo`}
                  className="h-16 w-16 rounded-lg object-cover border border-slate-100"
                />
              ) : (
                <div className="h-16 w-16 rounded-lg bg-slate-100 flex items-center justify-center text-slate-400 text-xl font-semibold">
                  {company.name[0]}
                </div>
              )}
              <div className="min-w-0">
                <h1 className="text-xl font-semibold text-slate-900">{company.name}</h1>
                <p className="mt-0.5 text-sm text-slate-500">
                  {[company.industry, company.location, company.company_size]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
                {company.website && (
                  <a
                    href={company.website}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 inline-block text-sm text-slate-600 hover:underline"
                  >
                    {company.website}
                  </a>
                )}
              </div>
            </div>

            {company.description && (
              <p className="mt-4 text-sm text-slate-600 leading-relaxed whitespace-pre-line">
                {company.description}
              </p>
            )}

            <h2 className="mt-8 text-sm font-semibold text-slate-900">
              Open roles ({company.open_jobs_count})
            </h2>
            <div className="mt-3 space-y-3">
              {jobs.length === 0 ? (
                <p className="text-sm text-slate-400">No open roles right now.</p>
              ) : (
                jobs.map((job) => <JobCard key={job.id} job={job} />)
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
