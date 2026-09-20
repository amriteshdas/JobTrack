import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  LineChart, Line, CartesianGrid,
} from "recharts";
import Navbar from "../../components/Navbar";
import StatCard from "../../components/StatCard";
import { useAuth } from "../../context/AuthContext";
import { dashboardService } from "../../services/dashboard";
import { formatEmploymentType, formatWorkMode } from "../../utils/format";

const STATUS_COLORS = {
  applied: "#94a3b8",
  under_review: "#60a5fa",
  shortlisted: "#fbbf24",
  interview: "#a78bfa",
  selected: "#34d399",
  rejected: "#f87171",
  withdrawn: "#cbd5e1",
};

export default function EmployerDashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    dashboardService
      .employer()
      .then(setData)
      .catch(() => setError("Could not load your dashboard. Please try refreshing."));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Employer</p>
            <h1 className="text-xl font-semibold text-slate-900">
              Welcome, {user.full_name || user.email}
            </h1>
          </div>
          <Link
            to="/employer/jobs/new"
            className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm font-medium hover:bg-slate-800"
          >
            Post a job
          </Link>
        </div>

        {error ? (
          <p className="text-sm text-red-600">{error}</p>
        ) : !data ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <StatCard label="Total jobs" value={data.stats.total_jobs} />
              <StatCard label="Active jobs" value={data.stats.active_jobs} />
              <StatCard label="Applications received" value={data.stats.applications_received} />
              <StatCard label="Shortlisted" value={data.stats.shortlisted} />
              <StatCard label="Interviews" value={data.stats.interviews_scheduled} />
            </div>

            <div className="grid md:grid-cols-2 gap-6 mt-8">
              <ChartCard title="Applications per job">
                {data.charts.applications_per_job.length === 0 ? (
                  <EmptyChart />
                ) : (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={data.charts.applications_per_job} layout="vertical" margin={{ left: 24 }}>
                      <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                      <YAxis
                        type="category"
                        dataKey="title"
                        width={120}
                        tick={{ fontSize: 12 }}
                        tickFormatter={(t) => (t.length > 16 ? `${t.slice(0, 16)}…` : t)}
                      />
                      <Tooltip />
                      <Bar dataKey="count" fill="#0f172a" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>

              <ChartCard title="Application status distribution">
                {data.charts.status_distribution.length === 0 ? (
                  <EmptyChart />
                ) : (
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={data.charts.status_distribution}
                        dataKey="count"
                        nameKey="status"
                        outerRadius={80}
                        label={({ status, count }) => `${status.replace("_", " ")}: ${count}`}
                      >
                        {data.charts.status_distribution.map((entry) => (
                          <Cell key={entry.status} fill={STATUS_COLORS[entry.status] || "#94a3b8"} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>

              <ChartCard title="Applications over time (last 30 days)" full>
                {data.charts.applications_over_time.length === 0 ? (
                  <EmptyChart />
                ) : (
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={data.charts.applications_over_time}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="count" stroke="#0f172a" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
            </div>

            <h2 className="text-sm font-semibold text-slate-900 mt-8 mb-3">Recently posted jobs</h2>
            <div className="space-y-2">
              {data.recently_posted_jobs.length === 0 && (
                <p className="text-sm text-slate-400">
                  No jobs posted yet.{" "}
                  <Link to="/employer/jobs/new" className="text-slate-900 font-medium hover:underline">
                    Post your first one
                  </Link>
                  .
                </p>
              )}
              {data.recently_posted_jobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between bg-white border border-slate-200 rounded-lg px-3 py-2.5"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-900">{job.title}</p>
                    <p className="text-xs text-slate-400">
                      {formatWorkMode(job.work_mode)} · {formatEmploymentType(job.employment_type)} ·{" "}
                      <span className="capitalize">{job.status}</span>
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Link
                      to={`/employer/jobs/${job.id}/edit`}
                      className="text-sm text-slate-600 font-medium hover:underline"
                    >
                      Edit
                    </Link>
                    <Link
                      to={`/employer/jobs/${job.id}/applicants`}
                      className="text-sm text-slate-900 font-medium hover:underline"
                    >
                      Applicants
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function ChartCard({ title, full, children }) {
  return (
    <div className={`bg-white border border-slate-200 rounded-xl p-4 ${full ? "md:col-span-2" : ""}`}>
      <h3 className="text-sm font-semibold text-slate-900 mb-2">{title}</h3>
      {children}
    </div>
  );
}

function EmptyChart() {
  return (
    <div className="h-[220px] flex items-center justify-center text-sm text-slate-400">
      No data yet.
    </div>
  );
}
