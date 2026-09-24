const PAGE_SIZE = 20;

/**
 * Takes DRF's pagination envelope directly ({count, next, previous}) rather
 * than reimplementing page-count math from scratch in two places.
 */
export default function Pagination({ count, page, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-3 mt-8">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="btn btn-secondary !py-1.5 !px-3 text-xs"
      >
        Previous
      </button>
      <span className="text-sm text-ink-500 tabular-nums">
        Page {page} of {totalPages}
      </span>
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="btn btn-secondary !py-1.5 !px-3 text-xs"
      >
        Next
      </button>
    </div>
  );
}
