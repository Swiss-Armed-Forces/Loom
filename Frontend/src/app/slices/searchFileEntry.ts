import type { GetFilePreviewResponse, GetFilesFileEntry } from "@app/api/index";
import type { SearchQuery } from "@features/common/utils/model";

/**
 * One entry of the `search.files` cache.
 *
 * Lives in its own module so the predicate below can be shared by the
 * selectors, the result list and the tour without pulling in the slice.
 */
export interface SearchFileEntry {
    meta: GetFilesFileEntry | null;
    preview: GetFilePreviewResponse | null;
    query: SearchQuery | null;
    stale?: boolean;
    temporary?: boolean;
}

/**
 * Whether an entry is a hit of the current query.
 *
 * `search.files` is a cache, not the result set: it also holds entries for open
 * tabs, fetched previews and the temporary highlight. `meta` is only ever
 * assigned from a search hit and is nulled whenever a new query arrives, so it
 * is what separates results from the rest. A stale entry keeps its `meta` and
 * stays a result — its card stays on screen.
 */
export const isLoadedResult = (file: SearchFileEntry) => file.meta !== null;
