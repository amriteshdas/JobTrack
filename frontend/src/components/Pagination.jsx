const PAGE_SIZE = 20;

/**
 * Takes DRF's pagination envelope directly ({count, next, previous}) rather
 * than reimplementing page-count math from scratch in two places.
 */
export default function Pagination({ count, page, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 disabled:opacity-40 hover:bg-slate-50"
      >
        Previous
      </button>
      <span className="text-sm text-slate-500">
        Page {page} of {totalPages}
      </span>
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 disabled:opacity-40 hover:bg-slate-50"
      >
        Next
      </button>
    </div>
  );
}
