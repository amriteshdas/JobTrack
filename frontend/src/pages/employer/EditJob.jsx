import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import JobForm from "../../components/JobForm";
import { jobsService, companiesService } from "../../services/jobs";

const STATUS_STYLES = {
  draft: "badge-neutral",
  published: "badge-green",
  closed: "badge-red",
};

export default function EditJob() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [job, setJob] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [error, setError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [actionPending, setActionPending] = useState(false);

  const load = () => {
    Promise.all([jobsService.get(id), companiesService.mine()])
      .then(([jobData, companyList]) => {
        setJob(jobData);
        setCompanies(companyList);
      })
      .catch((err) =>
        setError(err.response?.status === 404 ? "Job not found." : "Could not load this job.")
      );
  };

  useEffect(() => {
    load();
  }, [id]);

  const handleUpdate = async (payload) => {
    const updated = await jobsService.update(id, payload);
    setJob(updated);
  };

  const runAction = async (action) => {
    setActionPending(true);
    setActionError(null);
    try {
      await action();
      load();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Could not complete that action.");
    } finally {
      setActionPending(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Delete this job posting? This can't be undone.")) return;
    setActionPending(true);
    try {
      await jobsService.remove(id);
      navigate("/employer", { replace: true });
    } catch {
      setActionError("Could not delete this job.");
      setActionPending(false);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-canvas">
        <Navbar />
        <main className="max-w-2xl mx-auto px-6 py-8">
          <div className="card px-6 py-8">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </main>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-canvas">
        <Navbar />
        <main className="max-w-2xl mx-auto px-6 py-8">
          <div className="card p-6">
            <div className="skeleton h-5 w-1/3 mb-3" />
            <div className="skeleton h-4 w-2/3" />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 py-8">
        <Link to="/employer" className="text-sm font-medium text-ink-500 hover:text-violet-700 transition-colors">
          &larr; Back to dashboard
        </Link>

        <div className="flex items-center justify-between mt-2 mb-6">
          <h1 className="font-display text-xl font-extrabold text-ink-950">Edit job</h1>
          <span className={`badge ${STATUS_STYLES[job.status]}`}>{job.status}</span>
        </div>

        {actionError && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700 animate-pop">
            {actionError}
          </div>
        )}

        <div className="card p-6 mb-4 flex flex-wrap items-center gap-2 animate-fade-up">
          {job.status !== "published" && (
            <button
              disabled={actionPending}
              onClick={() => runAction(() => jobsService.publish(id))}
              className="btn btn-primary"
            >
              Publish
            </button>
          )}
          {job.status === "published" && (
            <button
              disabled={actionPending}
              onClick={() => runAction(() => jobsService.unpublish(id))}
              className="btn btn-secondary"
            >
              Unpublish (back to draft)
            </button>
          )}
          {job.status !== "closed" && (
            <button
              disabled={actionPending}
              onClick={() => runAction(() => jobsService.close(id))}
              className="btn btn-secondary"
            >
              Close job
            </button>
          )}
          <Link to={`/employer/jobs/${id}/applicants`} className="btn btn-secondary">
            View applicants
          </Link>
          <button
            disabled={actionPending}
            onClick={handleDelete}
            className="ml-auto text-sm font-medium text-ink-500 hover:text-red-600 disabled:opacity-50 transition-colors"
          >
            Delete job
          </button>
        </div>

        <div className="card p-6 animate-fade-up">
          <JobForm
            companies={companies}
            initial={{
              company: job.company,
              title: job.title,
              description: job.description,
              responsibilities: job.responsibilities,
              qualifications: job.qualifications,
              benefits: job.benefits,
              location: job.location,
              work_mode: job.work_mode,
              employment_type: job.employment_type,
              experience_required: job.experience_required,
              salary_min: job.salary_min ?? "",
              salary_max: job.salary_max ?? "",
              application_deadline: job.application_deadline || "",
              skills: job.skills.map((s) => s.name),
            }}
            onSubmit={handleUpdate}
            submitLabel="Save changes"
          />
        </div>
      </main>
    </div>
  );
}
