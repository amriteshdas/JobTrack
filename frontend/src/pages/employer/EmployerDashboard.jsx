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
  applied: "#b3a9cf",
  under_review: "#47bfff",
  shortlisted: "#f59e0b",
  interview: "#8b4dff",
  selected: "#22c58b",
  rejected: "#f87171",
  withdrawn: "#dcd0ff",
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
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6 animate-fade-up">
          <div>
            <p className="text-xs font-semibold text-violet-600">Employer</p>
            <h1 className="font-display text-xl font-extrabold text-ink-950 mt-0.5">
              Welcome, {user.full_name || user.email}
            </h1>
          </div>
          <Link to="/employer/jobs/new" className="btn btn-primary">
            Post a job
          </Link>
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
              <StatCard label="Total jobs" value={data.stats.total_jobs} index={0} />
              <StatCard label="Active jobs" value={data.stats.active_jobs} index={1} />
              <StatCard label="Applications received" value={data.stats.applications_received} index={2} />
              <StatCard label="Shortlisted" value={data.stats.shortlisted} index={3} />
              <StatCard label="Interviews" value={data.stats.interviews_scheduled} index={4} />
            </div>

            <div className="grid md:grid-cols-2 gap-6 mt-8">
              <ChartCard title="Applications per job">
                {data.charts.applications_per_job.length === 0 ? (
                  <EmptyChart />
                ) : (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={data.charts.applications_per_job} layout="vertical" margin={{ left: 24 }}>
                      <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: "#6b6285" }} />
                      <YAxis
                        type="category"
                        dataKey="title"
                        width={120}
                        tick={{ fontSize: 12, fill: "#6b6285" }}
                        tickFormatter={(t) => (t.length > 16 ? `${t.slice(0, 16)}…` : t)}
                      />
                      <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #ece7f7", fontSize: 13 }} />
                      <Bar dataKey="count" fill="#7c3aed" radius={[0, 6, 6, 0]} />
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
                          <Cell key={entry.status} fill={STATUS_COLORS[entry.status] || "#b3a9cf"} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #ece7f7", fontSize: 13 }} />
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
                      <CartesianGrid strokeDasharray="3 3" stroke="#ece7f7" />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#6b6285" }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#6b6285" }} />
                      <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #ece7f7", fontSize: 13 }} />
                      <Line type="monotone" dataKey="count" stroke="#7c3aed" strokeWidth={2.5} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
            </div>

            <h2 className="font-display text-sm font-bold text-ink-950 mt-8 mb-3">Recently posted jobs</h2>
            <div className="space-y-2">
              {data.recently_posted_jobs.length === 0 && (
                <p className="text-sm text-ink-500">
                  No jobs posted yet.{" "}
                  <Link to="/employer/jobs/new" className="text-violet-600 font-semibold hover:text-violet-800">
                    Post your first one
                  </Link>
                  .
                </p>
              )}
              {data.recently_posted_jobs.map((job, i) => (
                <div key={job.id} style={{ "--reveal-index": i }} className="reveal card card-hover flex items-center justify-between px-3.5 py-2.5">
                  <div>
                    <p className="text-sm font-semibold text-ink-950">{job.title}</p>
                    <p className="text-xs text-ink-500">
                      {formatWorkMode(job.work_mode)} · {formatEmploymentType(job.employment_type)} ·{" "}
                      <span className="capitalize">{job.status}</span>
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <Link to={`/employer/jobs/${job.id}/edit`} className="text-sm text-ink-700 font-medium hover:text-violet-700 transition-colors">
                      Edit
                    </Link>
                    <Link to={`/employer/jobs/${job.id}/applicants`} className="text-sm text-violet-600 font-semibold hover:text-violet-800 transition-colors">
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
    <div className={`card p-4 ${full ? "md:col-span-2" : ""}`}>
      <h3 className="font-display text-sm font-bold text-ink-950 mb-2">{title}</h3>
      {children}
    </div>
  );
}

function EmptyChart() {
  return (
    <div className="h-[220px] flex items-center justify-center text-sm text-ink-500">
      No data yet.
    </div>
  );
}
