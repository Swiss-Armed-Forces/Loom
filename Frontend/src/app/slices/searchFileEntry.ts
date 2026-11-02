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
    /** Field set `preview` was fetched for, see isPreviewFresh. */
    previewFields?: string[];
    /** When `preview` was fetched, as epoch milliseconds. */
    previewFetchedAt?: number;
}

/**
 * How long a cached preview is trusted before a card re-entering the viewport
 * refetches it.
 *
 * A card is only subscribed to its file's updates while it is on screen, so a
 * file that changes while its card is scrolled away delivers nothing and the
 * entry is never marked stale. This bounds how wrong an on-screen card can be
 * without needing a subscription for every loaded result. The refetch is
 * invisible: `fetchPreview.pending` leaves `preview` in place, so the card goes
 * on rendering the old data and swaps when the new arrives.
 */
export const PREVIEW_REVALIDATE_MS = 60_000;

export interface PreviewFreshness {
    /** The query whose results are on screen. */
    query: SearchQuery | null;
    /** The field set cards are currently rendering. */
    previewFields: string[];
    /** Defaults to now; injected by tests. */
    now?: number;
}

/**
 * Whether `entry`'s cached preview can be rendered as-is.
 *
 * One predicate for every caller, field set included: a copy that leaves the
 * field set out lets a card go on rendering the old set for as long as the
 * entry survives, however the selection changes.
 */
export const isPreviewFresh = (
    entry: SearchFileEntry | undefined,
    { query, previewFields, now = Date.now() }: PreviewFreshness,
): boolean => {
    if (entry?.preview == null || entry.stale) return false;
    if ((entry.query?.query ?? null) !== (query?.query ?? null)) return false;
    if (!sameFields(entry.previewFields, previewFields)) return false;
    return now - (entry.previewFetchedAt ?? 0) < PREVIEW_REVALIDATE_MS;
};

// Order is not significant: the field set is a selection, and the API is asked
// for it as a list only because that is what the query string carries.
const sameFields = (cached: string[] | undefined, current: string[]) => {
    if (cached === undefined || cached.length !== current.length) return false;
    const sortedCached = [...cached].sort();
    const sortedCurrent = [...current].sort();
    return sortedCached.every((field, i) => field === sortedCurrent[i]);
};

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
