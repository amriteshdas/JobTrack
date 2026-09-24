import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import JobCard from "../../components/JobCard";
import FilterSidebar from "../../components/FilterSidebar";
import Pagination from "../../components/Pagination";
import { useJobFilters } from "../../hooks/useJobFilters";
import { jobsService } from "../../services/jobs";

const SORT_OPTIONS = [
  { value: "-published_at", label: "Newest" },
  { value: "salary_min", label: "Salary: low to high" },
  { value: "-salary_min", label: "Salary: high to low" },
];

export default function Home() {
  const { filters, setFilters, page, setPage } = useJobFilters();
  const [data, setData] = useState({ count: 0, results: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Local text state for the search box so typing doesn't refetch on every
  // keystroke -- the request only fires on submit or when a filter/page
  // changes via the sidebar/pagination.
  const [searchInput, setSearchInput] = useState(filters.search || "");

  useEffect(() => {
    setSearchInput(filters.search || "");
  }, [filters.search]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    jobsService
      .list({ ...filters, page })
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load jobs. Is the backend running?");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [filters, page]);

  const submitSearch = (e) => {
    e.preventDefault();
    setFilters({ ...filters, search: searchInput });
  };

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />

      <div className="relative overflow-hidden border-b border-violet-100/70">
        <div className="absolute inset-0 bg-gradient-to-br from-violet-50 via-canvas to-sky-50" />
        <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-violet-200/40 blur-3xl" />
        <div className="absolute right-0 top-0 h-64 w-64 rounded-full bg-sky-200/40 blur-3xl" />

        <div className="relative max-w-6xl mx-auto px-6 py-14 sm:py-16">
          <p className="badge mb-4 animate-fade-up">Hiring, made simple</p>
          <h1 className="font-display text-3xl sm:text-4xl font-extrabold text-ink-950 max-w-xl animate-fade-up" style={{ animationDelay: "60ms" }}>
            Find your next role
          </h1>
          <p className="mt-2 text-ink-500 max-w-md animate-fade-up" style={{ animationDelay: "100ms" }}>
            Search open positions from companies that are actively hiring right now.
          </p>
          <form
            onSubmit={submitSearch}
            className="mt-6 flex gap-2 max-w-2xl animate-fade-up"
            style={{ animationDelay: "140ms" }}
          >
            <div className="relative flex-1">
              <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-500/60" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="7" />
                <path d="m21 21-4.3-4.3" />
              </svg>
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Job title, skill, or company"
                className="input pl-10 !py-3 shadow-soft"
              />
            </div>
            <button type="submit" className="btn btn-primary !px-6">
              Search
            </button>
          </form>
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-6 py-10 flex flex-col lg:flex-row gap-8">
        <FilterSidebar filters={filters} onChange={setFilters} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-ink-500">
              {loading ? "Searching…" : `${data.count} job${data.count === 1 ? "" : "s"} found`}
            </p>
            <select
              value={filters.ordering || "-published_at"}
              onChange={(e) => setFilters({ ...filters, ordering: e.target.value })}
              className="text-sm border border-violet-100 bg-white rounded-lg px-2.5 py-1.5 text-ink-700 focus:outline-none focus:border-violet-400"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 animate-pop">
              {error}
            </div>
          )}

          {loading && (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="card p-5 h-[104px]">
                  <div className="skeleton h-4 w-1/3 mb-3" />
                  <div className="skeleton h-3 w-1/2" />
                </div>
              ))}
            </div>
          )}

          {!error && !loading && data.results.length === 0 && (
            <div className="text-center py-16 animate-fade-in">
              <div className="mx-auto h-12 w-12 rounded-2xl bg-violet-50 grid place-items-center text-violet-400 mb-3">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="7" />
                  <path d="m21 21-4.3-4.3" />
                </svg>
              </div>
              <p className="text-ink-500 text-sm">No jobs match these filters. Try widening your search.</p>
            </div>
          )}

          {!loading && (
            <div className="space-y-3">
              {data.results.map((job, i) => (
                <JobCard key={job.id} job={job} index={i} />
              ))}
            </div>
          )}

          <Pagination count={data.count} page={page} onPageChange={setPage} />
        </div>
      </main>
    </div>
  );
}
