import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import SkillsInput from "../../components/SkillsInput";
import { profileService } from "../../services/profile";

const emptyEducation = { institution: "", degree: "", field_of_study: "", start_date: "", end_date: "" };
const emptyExperience = { company_name: "", title: "", start_date: "", end_date: "", description: "" };

export default function SeekerProfile() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [errors, setErrors] = useState({});

  const [newEducation, setNewEducation] = useState(emptyEducation);
  const [newExperience, setNewExperience] = useState(emptyExperience);

  const load = () => {
    profileService.getSeekerProfile().then((data) => {
      setProfile(data);
      setForm({
        headline: data.headline || "",
        bio: data.bio || "",
        location: data.location || "",
        years_of_experience: data.years_of_experience ?? 0,
        expected_salary: data.expected_salary ?? "",
        github_url: data.github_url || "",
        linkedin_url: data.linkedin_url || "",
        portfolio_url: data.portfolio_url || "",
      });
    });
  };

  useEffect(load, []);

  if (!profile || !form) {
    return (
      <Shell>
        <p className="text-sm text-slate-400">Loading…</p>
      </Shell>
    );
  }

  const saveBasics = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErrors({});
    setMessage(null);
    try {
      const updated = await profileService.updateSeekerProfile(form);
      setProfile(updated);
      setMessage("Profile saved.");
    } catch (err) {
      setErrors(err.response?.data || {});
    } finally {
      setSaving(false);
    }
  };

  const uploadFile = async (field, file) => {
    try {
      const updated = await profileService.updateSeekerProfile({ [field]: file });
      setProfile(updated);
      setMessage(field === "resume" ? "Resume uploaded." : "Photo uploaded.");
    } catch (err) {
      setErrors(err.response?.data || {});
    }
  };

  const saveSkills = async (skills) => {
    const updated = await profileService.setSkills(skills);
    setProfile(updated);
  };

  const addEducation = async (e) => {
    e.preventDefault();
    try {
      await profileService.addEducation({
        ...newEducation,
        end_date: newEducation.end_date || null,
      });
      setNewEducation(emptyEducation);
      load();
    } catch (err) {
      setErrors(err.response?.data || {});
    }
  };

  const addExperience = async (e) => {
    e.preventDefault();
    try {
      await profileService.addExperience({
        ...newExperience,
        end_date: newExperience.end_date || null,
      });
      setNewExperience(emptyExperience);
      load();
    } catch (err) {
      setErrors(err.response?.data || {});
    }
  };

  return (
    <Shell>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-slate-900">Your profile</h1>
        <Link to="/seeker/saved-jobs" className="text-sm text-slate-600 hover:underline">
          Saved jobs
        </Link>
      </div>

      {message && (
        <div className="mb-4 rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-2.5 text-sm text-emerald-700">
          {message}
        </div>
      )}

      {/* Basics */}
      <Card title="Basics">
        <form onSubmit={saveBasics} className="space-y-4">
          <Field label="Headline">
            <input
              value={form.headline}
              onChange={(e) => setForm({ ...form, headline: e.target.value })}
              placeholder="e.g. Backend Engineer, 3 years experience"
              className="input"
            />
          </Field>
          <Field label="About">
            <textarea
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
              rows={4}
              className="input"
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Location">
              <input
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                className="input"
              />
            </Field>
            <Field label="Years of experience">
              <input
                type="number"
                min="0"
                value={form.years_of_experience}
                onChange={(e) => setForm({ ...form, years_of_experience: e.target.value })}
                className="input"
              />
            </Field>
          </div>
          <Field label="Expected salary" error={errors.expected_salary}>
            <input
              type="number"
              min="0"
              value={form.expected_salary}
              onChange={(e) => setForm({ ...form, expected_salary: e.target.value })}
              className="input"
            />
          </Field>
          <div className="grid grid-cols-3 gap-4">
            <Field label="GitHub">
              <input
                value={form.github_url}
                onChange={(e) => setForm({ ...form, github_url: e.target.value })}
                className="input"
              />
            </Field>
            <Field label="LinkedIn">
              <input
                value={form.linkedin_url}
                onChange={(e) => setForm({ ...form, linkedin_url: e.target.value })}
                className="input"
              />
            </Field>
            <Field label="Portfolio">
              <input
                value={form.portfolio_url}
                onChange={(e) => setForm({ ...form, portfolio_url: e.target.value })}
                className="input"
              />
            </Field>
          </div>
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-slate-900 text-white px-5 py-2.5 text-sm font-medium hover:bg-slate-800 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </form>
      </Card>

      {/* Resume & photo */}
      <Card title="Resume">
        <p className="text-sm text-slate-500 mb-2">
          {profile.resume ? (
            <a href={profile.resume} target="_blank" rel="noreferrer" className="text-slate-900 hover:underline">
              View current resume
            </a>
          ) : (
            "No resume uploaded yet."
          )}
        </p>
        <input
          type="file"
          accept=".pdf,.doc,.docx"
          onChange={(e) => e.target.files[0] && uploadFile("resume", e.target.files[0])}
          className="text-sm"
        />
        {errors.resume && <p className="mt-1 text-xs text-red-600">{errors.resume}</p>}
      </Card>

      {/* Skills */}
      <Card title="Skills">
        <SkillsInput
          skills={profile.skills.map((s) => s.name)}
          onChange={saveSkills}
        />
      </Card>

      {/* Education */}
      <Card title="Education">
        <div className="space-y-3 mb-4">
          {profile.education.length === 0 && (
            <p className="text-sm text-slate-400">No education added yet.</p>
          )}
          {profile.education.map((edu) => (
            <div key={edu.id} className="flex items-center justify-between border border-slate-100 rounded-lg px-3 py-2">
              <div>
                <p className="text-sm font-medium text-slate-900">{edu.degree} · {edu.institution}</p>
                <p className="text-xs text-slate-400">
                  {edu.start_date} — {edu.end_date || "Present"}
                </p>
              </div>
              <button
                onClick={() => profileService.deleteEducation(edu.id).then(load)}
                className="text-xs text-slate-400 hover:text-red-600"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
        <form onSubmit={addEducation} className="grid grid-cols-2 gap-3">
          <input placeholder="Institution" value={newEducation.institution}
            onChange={(e) => setNewEducation({ ...newEducation, institution: e.target.value })}
            className="input" required />
          <input placeholder="Degree" value={newEducation.degree}
            onChange={(e) => setNewEducation({ ...newEducation, degree: e.target.value })}
            className="input" required />
          <input type="date" value={newEducation.start_date}
            onChange={(e) => setNewEducation({ ...newEducation, start_date: e.target.value })}
            className="input" required />
          <input type="date" value={newEducation.end_date}
            onChange={(e) => setNewEducation({ ...newEducation, end_date: e.target.value })}
            className="input" placeholder="Leave blank if ongoing" />
          <button type="submit" className="col-span-2 rounded-lg border border-slate-300 py-2 text-sm text-slate-700 hover:bg-slate-50">
            Add education
          </button>
        </form>
      </Card>

      {/* Experience */}
      <Card title="Experience">
        <div className="space-y-3 mb-4">
          {profile.experience.length === 0 && (
            <p className="text-sm text-slate-400">No experience added yet.</p>
          )}
          {profile.experience.map((exp) => (
            <div key={exp.id} className="flex items-center justify-between border border-slate-100 rounded-lg px-3 py-2">
              <div>
                <p className="text-sm font-medium text-slate-900">{exp.title} · {exp.company_name}</p>
                <p className="text-xs text-slate-400">
                  {exp.start_date} — {exp.is_current ? "Present" : exp.end_date}
                </p>
              </div>
              <button
                onClick={() => profileService.deleteExperience(exp.id).then(load)}
                className="text-xs text-slate-400 hover:text-red-600"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
        <form onSubmit={addExperience} className="grid grid-cols-2 gap-3">
          <input placeholder="Company" value={newExperience.company_name}
            onChange={(e) => setNewExperience({ ...newExperience, company_name: e.target.value })}
            className="input" required />
          <input placeholder="Title" value={newExperience.title}
            onChange={(e) => setNewExperience({ ...newExperience, title: e.target.value })}
            className="input" required />
          <input type="date" value={newExperience.start_date}
            onChange={(e) => setNewExperience({ ...newExperience, start_date: e.target.value })}
            className="input" required />
          <input type="date" value={newExperience.end_date}
            onChange={(e) => setNewExperience({ ...newExperience, end_date: e.target.value })}
            className="input" placeholder="Leave blank if current" />
          <textarea placeholder="Description" value={newExperience.description}
            onChange={(e) => setNewExperience({ ...newExperience, description: e.target.value })}
            className="input col-span-2" rows={2} />
          <button type="submit" className="col-span-2 rounded-lg border border-slate-300 py-2 text-sm text-slate-700 hover:bg-slate-50">
            Add experience
          </button>
        </form>
      </Card>
    </Shell>
  );
}

function Shell({ children }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 py-8">{children}</main>
      <style>{`.input { width: 100%; border: 1px solid rgb(203 213 225); border-radius: 0.5rem; padding: 0.5rem 0.75rem; font-size: 0.875rem; } .input:focus { outline: none; border-color: rgb(148 163 184); }`}</style>
    </div>
  );
}

function Card({ title, children }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 mb-5">
      <h2 className="text-sm font-semibold text-slate-900 mb-3">{title}</h2>
      {children}
    </div>
  );
}

function Field({ label, error, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
