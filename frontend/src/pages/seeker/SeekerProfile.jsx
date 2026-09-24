import { useEffect, useRef, useState } from "react";
import Navbar from "../../components/Navbar";
import SkillsInput from "../../components/SkillsInput";
import { profileService } from "../../services/profile";

const emptyEducation = { institution: "", degree: "", field_of_study: "", start_date: "", end_date: "" };
const emptyExperience = { company_name: "", title: "", start_date: "", end_date: "", description: "" };

/**
 * A LinkedIn-style layout: read-only display is the default state for
 * every section, with a small "Edit" affordance that swaps just that
 * section into an editable form -- rather than one long always-editable
 * form (the previous design). This matches how people actually expect a
 * profile page to behave: mostly for reading (by the person themselves,
 * or by an employer via the applicant view), occasionally edited one
 * section at a time.
 */
export default function SeekerProfile() {
  const [profile, setProfile] = useState(null);
  const [message, setMessage] = useState(null);
  const [globalError, setGlobalError] = useState(null);

  const load = () => {
    profileService
      .getSeekerProfile()
      .then(setProfile)
      .catch(() => setGlobalError("Could not load your profile. Please refresh."));
  };

  useEffect(() => {
    load();
  }, []);

  const flash = (text) => {
    setMessage(text);
    setTimeout(() => setMessage(null), 3000);
  };

  if (globalError) {
    return (
      <Shell>
        <div className="card px-6 py-8">
          <p className="text-sm text-red-600">{globalError}</p>
        </div>
      </Shell>
    );
  }

  if (!profile) {
    return (
      <Shell>
        <div className="card p-5 mb-5">
          <div className="flex items-start gap-5">
            <div className="skeleton h-24 w-24 rounded-full shrink-0" />
            <div className="flex-1">
              <div className="skeleton h-5 w-1/2 mb-2" />
              <div className="skeleton h-3.5 w-1/3" />
            </div>
          </div>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      {message && (
        <div className="mb-4 rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-2.5 text-sm text-emerald-700 animate-pop">
          {message}
        </div>
      )}

      <ProfileHeader profile={profile} onUpdated={setProfile} onSaved={() => flash("Profile updated.")} />
      <AboutCard profile={profile} onUpdated={setProfile} onSaved={() => flash("Profile updated.")} />
      <ResumeCard profile={profile} onUpdated={setProfile} onSaved={() => flash("Resume uploaded.")} />
      <SkillsCard profile={profile} onUpdated={setProfile} />
      <EducationCard profile={profile} onReload={load} onSaved={() => flash("Education updated.")} />
      <ExperienceCard profile={profile} onReload={load} onSaved={() => flash("Experience updated.")} />
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// Header: photo, name, headline, location, links -- the "top card" LinkedIn
// profiles open with.
// ---------------------------------------------------------------------------

function ProfileHeader({ profile, onUpdated, onSaved }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(null);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const fileInputRef = useRef(null);

  const startEdit = () => {
    setForm({
      headline: profile.headline || "",
      location: profile.location || "",
      years_of_experience: profile.years_of_experience ?? 0,
      expected_salary: profile.expected_salary ?? "",
      github_url: profile.github_url || "",
      linkedin_url: profile.linkedin_url || "",
      portfolio_url: profile.portfolio_url || "",
    });
    setErrors({});
    setEditing(true);
  };

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErrors({});
    try {
      const updated = await profileService.updateSeekerProfile(form);
      onUpdated(updated);
      setEditing(false);
      onSaved();
    } catch (err) {
      setErrors(err.response?.data || {});
    } finally {
      setSaving(false);
    }
  };

  const handlePhotoChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadingPhoto(true);
    try {
      const updated = await profileService.updateSeekerProfile({ profile_photo: file });
      onUpdated(updated);
      onSaved();
    } catch {
      alert("Could not upload photo. Make sure it's an image under 2MB.");
    } finally {
      setUploadingPhoto(false);
      e.target.value = "";
    }
  };

  const links = [
    profile.github_url && { label: "GitHub", url: profile.github_url },
    profile.linkedin_url && { label: "LinkedIn", url: profile.linkedin_url },
    profile.portfolio_url && { label: "Portfolio", url: profile.portfolio_url },
  ].filter(Boolean);

  return (
    <Card>
      <div className="flex items-start gap-5">
        <div className="relative shrink-0 group">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="block h-24 w-24 rounded-full overflow-hidden bg-gradient-to-br from-violet-100 to-sky-100 border border-violet-100 shadow-soft transition-transform group-hover:scale-105"
            title="Change profile photo"
          >
            {profile.profile_photo ? (
              <img src={profile.profile_photo} alt="" className="h-full w-full object-cover" />
            ) : (
              <span className="h-full w-full flex items-center justify-center text-2xl font-display font-bold text-violet-500">
                {(profile.full_name || profile.email)[0]?.toUpperCase()}
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadingPhoto}
            className="absolute bottom-0 right-0 h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-violet-700 text-white flex items-center justify-center text-xs hover:brightness-110 disabled:opacity-50 border-2 border-white shadow-soft transition-transform hover:scale-110"
            title="Change profile photo"
          >
            {uploadingPhoto ? "…" : "\u270E"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handlePhotoChange}
            className="hidden"
          />
        </div>

        <div className="flex-1 min-w-0">
          {!editing ? (
            <>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h1 className="text-xl font-semibold text-ink-950">{profile.full_name || profile.email}</h1>
                  {profile.headline && <p className="text-sm text-ink-700 mt-0.5">{profile.headline}</p>}
                  {profile.location && <p className="text-sm text-ink-500 mt-0.5">{profile.location}</p>}
                </div>
                <button
                  onClick={startEdit}
                  className="shrink-0 text-sm font-medium text-violet-600 hover:text-violet-800"
                >
                  Edit
                </button>
              </div>

              {links.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-3">
                  {links.map((l) => (
                    <a
                      key={l.label}
                      href={l.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm font-medium text-violet-600 hover:text-violet-800"
                    >
                      {l.label}
                    </a>
                  ))}
                </div>
              )}

              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-500">
                <span>{profile.years_of_experience} yr{profile.years_of_experience === 1 ? "" : "s"} experience</span>
                {profile.expected_salary && (
                  <span>Expected: ₹{(profile.expected_salary / 100000).toFixed(1)}L</span>
                )}
              </div>
            </>
          ) : (
            <form onSubmit={save} className="space-y-3">
              <Field label="Headline">
                <input
                  value={form.headline}
                  onChange={(e) => setForm({ ...form, headline: e.target.value })}
                  placeholder="e.g. Backend Engineer, 3 years experience"
                  className="input"
                />
              </Field>
              <div className="grid grid-cols-2 gap-3">
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
              <div className="grid grid-cols-3 gap-3">
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
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="btn btn-primary"
                >
                  {saving ? "Saving…" : "Save"}
                </button>
                <button
                  type="button"
                  onClick={() => setEditing(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// About (bio)
// ---------------------------------------------------------------------------

function AboutCard({ profile, onUpdated, onSaved }) {
  const [editing, setEditing] = useState(false);
  const [bio, setBio] = useState(profile.bio || "");
  const [saving, setSaving] = useState(false);

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await profileService.updateSeekerProfile({ bio });
      onUpdated(updated);
      setEditing(false);
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card title="About" onEdit={!editing ? () => { setBio(profile.bio || ""); setEditing(true); } : undefined}>
      {!editing ? (
        profile.bio ? (
          <p className="text-sm text-ink-700 whitespace-pre-line">{profile.bio}</p>
        ) : (
          <p className="text-sm text-ink-500">
            Tell employers a bit about yourself -- click Edit to add a summary.
          </p>
        )
      ) : (
        <form onSubmit={save} className="space-y-3">
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            rows={4}
            className="input"
            autoFocus
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="btn btn-primary"
            >
              {saving ? "Saving…" : "Save"}
            </button>
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Resume
// ---------------------------------------------------------------------------

function ResumeCard({ profile, onUpdated, onSaved }) {
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const upload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setError(null);
    try {
      const updated = await profileService.updateSeekerProfile({ resume: file });
      onUpdated(updated);
      onSaved();
    } catch (err) {
      setError(err.response?.data?.resume?.[0] || "Could not upload resume.");
    } finally {
      e.target.value = "";
    }
  };

  return (
    <Card title="Resume">
      <p className="text-sm text-ink-500 mb-2">
        {profile.resume ? (
          <a href={profile.resume} target="_blank" rel="noreferrer" className="text-violet-700 font-semibold hover:text-violet-800">
            View current resume
          </a>
        ) : (
          "No resume uploaded yet. This is used by default when you apply to jobs."
        )}
      </p>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="btn btn-secondary !py-1.5 !px-3 text-xs"
        >
          {profile.resume ? "Change resume" : "Upload resume"}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.doc,.docx"
          onChange={upload}
          className="hidden"
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Skills -- the chip input is already an in-place editor, so no separate
// view/edit toggle is needed here.
// ---------------------------------------------------------------------------

function SkillsCard({ profile, onUpdated }) {
  const saveSkills = async (skills) => {
    const updated = await profileService.setSkills(skills);
    onUpdated(updated);
  };

  return (
    <Card title="Skills">
      <SkillsInput skills={profile.skills.map((s) => s.name)} onChange={saveSkills} />
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Education -- list of entries, each independently editable in place
// ---------------------------------------------------------------------------

function EducationCard({ profile, onReload, onSaved }) {
  const [editingId, setEditingId] = useState(null);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState(emptyEducation);
  const [error, setError] = useState(null);

  const startEdit = (edu) => {
    setForm({
      institution: edu.institution,
      degree: edu.degree,
      field_of_study: edu.field_of_study || "",
      start_date: edu.start_date,
      end_date: edu.end_date || "",
    });
    setEditingId(edu.id);
    setAdding(false);
    setError(null);
  };

  const startAdd = () => {
    setForm(emptyEducation);
    setAdding(true);
    setEditingId(null);
    setError(null);
  };

  const cancel = () => {
    setEditingId(null);
    setAdding(false);
  };

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    const payload = { ...form, end_date: form.end_date || null };
    try {
      if (editingId) await profileService.updateEducation(editingId, payload);
      else await profileService.addEducation(payload);
      cancel();
      onReload();
      onSaved();
    } catch (err) {
      setError(err.response?.data?.end_date?.[0] || "Could not save this entry.");
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Remove this education entry?")) return;
    await profileService.deleteEducation(id);
    onReload();
  };

  return (
    <Card title="Education" onEdit={!adding ? startAdd : undefined} editLabel="+ Add">
      <div className="space-y-2">
        {profile.education.length === 0 && !adding && (
          <p className="text-sm text-ink-500">No education added yet.</p>
        )}
        {profile.education.map((edu) =>
          editingId === edu.id ? (
            <EntryForm
              key={edu.id}
              error={error}
              fields={[
                { key: "institution", label: "Institution", required: true },
                { key: "degree", label: "Degree", required: true },
                { key: "field_of_study", label: "Field of study" },
              ]}
              form={form}
              setForm={setForm}
              onSubmit={submit}
              onCancel={cancel}
            />
          ) : (
            <div
              key={edu.id}
              className="flex items-center justify-between border border-violet-50 rounded-lg px-3 py-2.5 hover:bg-violet-50/40 transition-colors"
            >
              <div>
                <p className="text-sm font-medium text-ink-950">
                  {edu.degree}
                  {edu.field_of_study && ` in ${edu.field_of_study}`} · {edu.institution}
                </p>
                <p className="text-xs text-ink-500">
                  {edu.start_date} — {edu.end_date || "Present"}
                </p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <button onClick={() => startEdit(edu)} className="text-xs font-medium text-violet-600 hover:text-violet-800">
                  Edit
                </button>
                <button onClick={() => remove(edu.id)} className="text-xs font-medium text-ink-500 hover:text-red-600">
                  Remove
                </button>
              </div>
            </div>
          )
        )}
        {adding && (
          <EntryForm
            error={error}
            fields={[
              { key: "institution", label: "Institution", required: true },
              { key: "degree", label: "Degree", required: true },
              { key: "field_of_study", label: "Field of study" },
            ]}
            form={form}
            setForm={setForm}
            onSubmit={submit}
            onCancel={cancel}
          />
        )}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Experience -- same in-place edit pattern as Education
// ---------------------------------------------------------------------------

function ExperienceCard({ profile, onReload, onSaved }) {
  const [editingId, setEditingId] = useState(null);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState(emptyExperience);
  const [error, setError] = useState(null);

  const startEdit = (exp) => {
    setForm({
      company_name: exp.company_name,
      title: exp.title,
      start_date: exp.start_date,
      end_date: exp.end_date || "",
      description: exp.description || "",
    });
    setEditingId(exp.id);
    setAdding(false);
    setError(null);
  };

  const startAdd = () => {
    setForm(emptyExperience);
    setAdding(true);
    setEditingId(null);
    setError(null);
  };

  const cancel = () => {
    setEditingId(null);
    setAdding(false);
  };

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    const payload = { ...form, end_date: form.end_date || null };
    try {
      if (editingId) await profileService.updateExperience(editingId, payload);
      else await profileService.addExperience(payload);
      cancel();
      onReload();
      onSaved();
    } catch (err) {
      setError(err.response?.data?.end_date?.[0] || "Could not save this entry.");
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Remove this experience entry?")) return;
    await profileService.deleteExperience(id);
    onReload();
  };

  return (
    <Card title="Experience" onEdit={!adding ? startAdd : undefined} editLabel="+ Add">
      <div className="space-y-2">
        {profile.experience.length === 0 && !adding && (
          <p className="text-sm text-ink-500">No experience added yet.</p>
        )}
        {profile.experience.map((exp) =>
          editingId === exp.id ? (
            <EntryForm
              key={exp.id}
              error={error}
              fields={[
                { key: "company_name", label: "Company", required: true },
                { key: "title", label: "Title", required: true },
                { key: "description", label: "Description", textarea: true },
              ]}
              form={form}
              setForm={setForm}
              onSubmit={submit}
              onCancel={cancel}
            />
          ) : (
            <div
              key={exp.id}
              className="flex items-center justify-between border border-violet-50 rounded-lg px-3 py-2.5 hover:bg-violet-50/40 transition-colors"
            >
              <div>
                <p className="text-sm font-medium text-ink-950">
                  {exp.title} · {exp.company_name}
                </p>
                <p className="text-xs text-ink-500">
                  {exp.start_date} — {exp.is_current ? "Present" : exp.end_date}
                </p>
                {exp.description && <p className="text-sm text-ink-500 mt-0.5">{exp.description}</p>}
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <button onClick={() => startEdit(exp)} className="text-xs font-medium text-violet-600 hover:text-violet-800">
                  Edit
                </button>
                <button onClick={() => remove(exp.id)} className="text-xs font-medium text-ink-500 hover:text-red-600">
                  Remove
                </button>
              </div>
            </div>
          )
        )}
        {adding && (
          <EntryForm
            error={error}
            fields={[
              { key: "company_name", label: "Company", required: true },
              { key: "title", label: "Title", required: true },
              { key: "description", label: "Description", textarea: true },
            ]}
            form={form}
            setForm={setForm}
            onSubmit={submit}
            onCancel={cancel}
          />
        )}
      </div>
    </Card>
  );
}

/** Shared mini-form for one education or experience entry (add or edit). */
function EntryForm({ fields, form, setForm, onSubmit, onCancel, error }) {
  return (
    <form onSubmit={onSubmit} className="border border-violet-100 rounded-xl p-3.5 space-y-2.5 bg-violet-50/40 animate-pop">
      {error && <p className="text-xs text-red-600">{error}</p>}
      {fields.map((f) =>
        f.textarea ? (
          <textarea
            key={f.key}
            placeholder={f.label}
            value={form[f.key]}
            onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
            className="input"
            rows={2}
          />
        ) : (
          <input
            key={f.key}
            placeholder={f.label}
            value={form[f.key]}
            onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
            required={f.required}
            className="input"
          />
        )
      )}
      <div className="grid grid-cols-2 gap-2">
        <input
          type="date"
          value={form.start_date}
          onChange={(e) => setForm({ ...form, start_date: e.target.value })}
          required
          className="input"
        />
        <input
          type="date"
          value={form.end_date}
          onChange={(e) => setForm({ ...form, end_date: e.target.value })}
          placeholder="Leave blank if ongoing"
          className="input"
        />
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          className="btn btn-primary !py-1.5 !px-3 text-xs"
        >
          Save
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="btn btn-secondary !py-1.5 !px-3 text-xs"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function Shell({ children }) {
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}

function Card({ title, children, onEdit, editLabel = "Edit" }) {
  return (
    <div className="bg-white border border-violet-100 rounded-2xl p-5 mb-5">
      {title && (
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-ink-950">{title}</h2>
          {onEdit && (
            <button onClick={onEdit} className="text-sm font-medium text-violet-600 hover:text-violet-800">
              {editLabel}
            </button>
          )}
        </div>
      )}
      {children}
    </div>
  );
}

function Field({ label, error, children }) {
  return (
    <div>
      <label className="field-label">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-red-600 animate-fade-in">{error}</p>}
    </div>
  );
}
