import { Link } from "react-router-dom";
import { formatEmploymentType, formatSalary, formatWorkMode, timeAgo } from "../utils/format";

export default function JobCard({ job }) {
  const salary = formatSalary(job.salary_min, job.salary_max);

  return (
    <Link
      to={`/jobs/${job.id}`}
      className="block bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-300 hover:shadow-sm transition"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="font-semibold text-slate-900 truncate">{job.title}</h3>
          <p className="mt-0.5 text-sm text-slate-500 truncate">
            {job.company_name} · {job.location}
          </p>
        </div>
        <span className="shrink-0 text-xs text-slate-400">{timeAgo(job.published_at)}</span>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        <Tag>{formatWorkMode(job.work_mode)}</Tag>
        <Tag>{formatEmploymentType(job.employment_type)}</Tag>
        {salary && <Tag>{salary}</Tag>}
        {job.experience_required > 0 && (
          <Tag>{job.experience_required}+ yrs</Tag>
        )}
      </div>

      {job.skills?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {job.skills.slice(0, 5).map((skill) => (
            <span
              key={skill.id}
              className="text-xs text-slate-500 bg-slate-50 rounded px-2 py-0.5"
            >
              {skill.name}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}

function Tag({ children }) {
  return (
    <span className="text-xs font-medium text-slate-600 bg-slate-100 rounded-full px-2.5 py-1">
      {children}
    </span>
  );
}
