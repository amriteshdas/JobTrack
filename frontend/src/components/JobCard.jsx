import { Link } from "react-router-dom";
import { formatEmploymentType, formatSalary, formatWorkMode, timeAgo } from "../utils/format";

export default function JobCard({ job, index = 0 }) {
  const salary = formatSalary(job.salary_min, job.salary_max);

  return (
    <Link
      to={`/jobs/${job.id}`}
      style={{ "--reveal-index": index }}
      className="reveal card card-hover group block p-5"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="font-display font-bold text-ink-950 truncate group-hover:text-violet-700 transition-colors">
            {job.title}
          </h3>
          <p className="mt-1 text-sm text-ink-500 truncate">
            {job.company_name} · {job.location}
          </p>
        </div>
        <span className="shrink-0 text-xs text-ink-500/70 mt-0.5">{timeAgo(job.published_at)}</span>
      </div>

      <div className="mt-3.5 flex flex-wrap gap-1.5">
        <Tag>{formatWorkMode(job.work_mode)}</Tag>
        <Tag>{formatEmploymentType(job.employment_type)}</Tag>
        {salary && <Tag accent>{salary}</Tag>}
        {job.experience_required > 0 && <Tag>{job.experience_required}+ yrs</Tag>}
      </div>

      {job.skills?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {job.skills.slice(0, 5).map((skill) => (
            <span key={skill.id} className="text-xs text-ink-500 bg-violet-50/60 rounded-md px-2 py-0.5">
              {skill.name}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}

function Tag({ children, accent }) {
  return <span className={`badge ${accent ? "badge-sky" : "badge-neutral"}`}>{children}</span>;
}
