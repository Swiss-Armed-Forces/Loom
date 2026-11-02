import type { VisibleRange } from "@app/slices/searchSlice";

/**
 * How close to the end of what is loaded the next page is asked for.
 *
 * Rows rather than pixels: a pixel margin is three rows of a compact card and
 * one and a half of a full one, so the lead quietly shrinks exactly where rows
 * are tallest and a page takes longest to cross. Roughly a third of a page,
 * which is the room a request needs to return before the user arrives.
 */
export const PAGE_LEAD_ROWS = 8;

export interface NextPageTriggerInput {
    /** The rows on screen, or null before the list has reported any. */
    visibleRange: VisibleRange | null;
    /** Rows loaded so far. */
    loadedCount: number;
    hasMore: boolean;
    isPaginating: boolean;
    /** A page request has failed and is waiting on the user. */
    hasError: boolean;
    leadRows?: number;
}

/**
 * Whether the next page should be fetched now.
 *
 * Driven by where the user is in the list rather than by a sentinel element
 * coming into view, which also means a list shorter than the viewport fills
 * itself: its last row is on screen from the start.
 *
 * A failure stops this. Retrying a failing request once per scroll would
 * hammer the API, and a list that quietly stopped growing cannot be told apart
 * from one that has reached the end — so the button takes over.
 */
export const shouldFetchNextPage = ({
    visibleRange,
    loadedCount,
    hasMore,
    isPaginating,
    hasError,
    leadRows = PAGE_LEAD_ROWS,
}: NextPageTriggerInput): boolean => {
    if (!hasMore || isPaginating || hasError) return false;
    if (visibleRange === null || loadedCount === 0) return false;
    return visibleRange.endIndex >= loadedCount - 1 - leadRows;
};
