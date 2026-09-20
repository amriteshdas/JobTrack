import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import JobForm from "../../components/JobForm";
import { jobsService, companiesService } from "../../services/jobs";

const STATUS_STYLES = {
  draft: "bg-slate-100 text-slate-600",
  published: "bg-emerald-50 text-emerald-700",
  closed: "bg-red-50 text-red-700",
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
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <main className="max-w-2xl mx-auto px-6 py-8">
          <p className="text-sm text-red-600">{error}</p>
        </main>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <main className="max-w-2xl mx-auto px-6 py-8">
          <p className="text-sm text-slate-400">Loading…</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 py-8">
        <Link to="/employer" className="text-sm text-slate-500 hover:underline">
          &larr; Back to dashboard
        </Link>

        <div className="flex items-center justify-between mt-2 mb-6">
          <h1 className="text-xl font-semibold text-slate-900">Edit job</h1>
          <span className={`text-xs font-medium rounded-full px-2.5 py-1 ${STATUS_STYLES[job.status]}`}>
            {job.status}
          </span>
        </div>

        {actionError && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
            {actionError}
          </div>
        )}

        <div className="bg-white border border-slate-200 rounded-2xl p-6 mb-4 flex flex-wrap gap-2">
          {job.status !== "published" && (
            <button
              disabled={actionPending}
              onClick={() => runAction(() => jobsService.publish(id))}
              className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm font-medium hover:bg-slate-800 disabled:opacity-50"
            >
              Publish
            </button>
          )}
          {job.status === "published" && (
            <button
              disabled={actionPending}
              onClick={() => runAction(() => jobsService.unpublish(id))}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Unpublish (back to draft)
            </button>
          )}
          {job.status !== "closed" && (
            <button
              disabled={actionPending}
              onClick={() => runAction(() => jobsService.close(id))}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Close job
            </button>
          )}
          <Link
            to={`/employer/jobs/${id}/applicants`}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            View applicants
          </Link>
          <button
            disabled={actionPending}
            onClick={handleDelete}
            className="ml-auto text-sm text-slate-400 hover:text-red-600 disabled:opacity-50"
          >
            Delete job
          </button>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-6">
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
