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
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <div className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <h1 className="text-2xl font-semibold text-slate-900">
            Find your next role
          </h1>
          <form onSubmit={submitSearch} className="mt-4 flex gap-2 max-w-2xl">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Job title, skill, or company"
              className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:border-slate-400"
            />
            <button
              type="submit"
              className="rounded-lg bg-slate-900 text-white px-5 py-2.5 text-sm font-medium hover:bg-slate-800"
            >
              Search
            </button>
          </form>
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-6 py-8 flex flex-col lg:flex-row gap-8">
        <FilterSidebar filters={filters} onChange={setFilters} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-slate-500">
              {loading ? "Searching…" : `${data.count} job${data.count === 1 ? "" : "s"} found`}
            </p>
            <select
              value={filters.ordering || "-published_at"}
              onChange={(e) => setFilters({ ...filters, ordering: e.target.value })}
              className="text-sm border border-slate-300 rounded-lg px-2 py-1.5 focus:outline-none"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {!error && !loading && data.results.length === 0 && (
            <div className="text-center py-16 text-slate-400 text-sm">
              No jobs match these filters. Try widening your search.
            </div>
          )}

          <div className="space-y-3">
            {data.results.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>

          <Pagination count={data.count} page={page} onPageChange={setPage} />
        </div>
      </main>
    </div>
  );
}
