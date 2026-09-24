export default function StatCard({ label, value, icon, index = 0 }) {
  return (
    <div
      style={{ "--reveal-index": index }}
      className="reveal card p-5 relative overflow-hidden"
    >
      <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-violet-100/60 blur-xl" />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="font-display text-2xl font-extrabold text-ink-950 tabular-nums">{value}</p>
          <p className="text-xs font-medium text-ink-500 mt-1">{label}</p>
        </div>
        {icon && (
          <span className="grid place-items-center h-8 w-8 rounded-lg bg-violet-50 text-violet-600 text-sm">
            {icon}
          </span>
        )}
      </div>
    </div>
  );
}
