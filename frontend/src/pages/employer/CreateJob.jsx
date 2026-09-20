import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import JobForm from "../../components/JobForm";
import CreateCompanyForm from "../../components/CreateCompanyForm";
import { jobsService, companiesService } from "../../services/jobs";

export default function CreateJob() {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState(null);

  const loadCompanies = () =>
    companiesService.mine().then(setCompanies).catch(() => setCompanies([]));

  useEffect(() => {
    loadCompanies();
  }, []);

  const handleCreate = async (payload) => {
    const job = await jobsService.create(payload);
    // New jobs are created as drafts (see Job.Status default, Phase 3) --
    // land on the edit page so the employer can review and publish, rather
    // than assuming they want it live immediately.
    navigate(`/employer/jobs/${job.id}/edit`, { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 py-8">
        <Link to="/employer" className="text-sm text-slate-500 hover:underline">
          &larr; Back to dashboard
        </Link>
        <h1 className="mt-2 text-xl font-semibold text-slate-900 mb-6">Post a job</h1>

        {companies === null && <p className="text-sm text-slate-400">Loading…</p>}

        {companies?.length === 0 && (
          <CreateCompanyForm onCreated={() => loadCompanies()} />
        )}

        {companies?.length > 0 && (
          <div className="bg-white border border-slate-200 rounded-2xl p-6">
            <JobForm
              companies={companies}
              initial={companies.length === 1 ? { company: companies[0].id } : {}}
              onSubmit={handleCreate}
              submitLabel="Create job (as draft)"
            />
          </div>
        )}
      </main>
    </div>
  );
}
