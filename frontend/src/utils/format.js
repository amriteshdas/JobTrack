const WORK_MODE_LABELS = { remote: "Remote", hybrid: "Hybrid", onsite: "On-site" };
const EMPLOYMENT_TYPE_LABELS = {
  full_time: "Full-time",
  part_time: "Part-time",
  internship: "Internship",
  contract: "Contract",
};

export function formatWorkMode(value) {
  return WORK_MODE_LABELS[value] || value;
}

export function formatEmploymentType(value) {
  return EMPLOYMENT_TYPE_LABELS[value] || value;
}

export function formatSalary(min, max) {
  if (!min && !max) return null;
  const fmt = (n) => `₹${(n / 100000).toFixed(1)}L`;
  if (min && max) return `${fmt(min)} - ${fmt(max)}`;
  return fmt(min || max);
}

export function timeAgo(dateString) {
  if (!dateString) return "";
  const diffMs = Date.now() - new Date(dateString).getTime();
  const days = Math.floor(diffMs / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 30) return `${days}d ago`;
  return new Date(dateString).toLocaleDateString();
}
