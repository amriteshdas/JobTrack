import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * Filters live in the URL (via useSearchParams), not in component state.
 *
 * Why: it makes the current search bookmarkable and shareable ("look at
 * these remote Django jobs" is a real URL a user can send someone), it
 * survives a page refresh, and the browser back button naturally undoes the
 * last filter change -- all for free, without writing any of that
 * ourselves.
 */
export function useJobFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = useMemo(() => Object.fromEntries(searchParams.entries()), [searchParams]);

  const setFilters = useCallback(
    (next) => {
      // Changing a filter always resets to page 1 -- staying on page 3 of a
      // now-different, likely-shorter result set would show an empty page.
      const { page, ...rest } = next;
      setSearchParams(rest);
    },
    [setSearchParams],
  );

  const setPage = useCallback(
    (page) => {
      setSearchParams({ ...filters, page: String(page) });
    },
    [filters, setSearchParams],
  );

  const page = parseInt(filters.page || "1", 10);

  return { filters, setFilters, page, setPage };
}
