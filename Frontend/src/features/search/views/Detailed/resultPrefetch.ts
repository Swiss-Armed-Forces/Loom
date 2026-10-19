/**
 * Which rows to have a preview ready for, ahead of the user reaching them.
 *
 * A row's preview is only fetched once the row is on screen, so scrolling
 * brings up cards with nothing in them yet. Fetching ahead of the viewport is
 * what makes the list read as continuous.
 *
 * Expressed in rows derived from the viewport rather than in pixels, so it
 * means the same at every spacing: 600px is three rows of a compact card and
 * one and a half of a full one.
 *
 * Pure, and kept apart from the hook, because jsdom has no layout engine and
 * these are the rules rather than the measurements.
 */

/** Which way the list is travelling; `null` before it has moved. */
export type ScrollDirection = "forward" | "backward" | null;

/** Viewports of lead kept in the direction of travel. */
export const LEAD_VIEWPORTS = 1.5;

/** Viewports kept warm behind the user, for a change of mind. */
export const TRAIL_VIEWPORTS = 0.5;

/**
 * Above this, speculation stops paying.
 *
 * Screenfuls a second, which is what "fast" means to the person scrolling: a
 * screen a second reads the same whether its rows are 40px or 400px. Rows a
 * second does not work — measured, an unhurried read of a dense list is 16
 * rows a second and a leisurely read of a loose one is 2, so a row threshold
 * switches the lead off exactly where the rows are shortest and most of them
 * are needed.
 *
 * Past this the rows are gone before a request for them could return, and
 * those requests queue ahead of the ones for the rows the user stops on — so
 * speculating through a fling does not merely waste calls, it slows the
 * landing.
 */
export const MAX_PREFETCH_VIEWPORTS_PER_SECOND = 1.5;

/**
 * Speculative preview requests allowed to be outstanding at once.
 *
 * The window says which rows are worth having; this says how fast to ask for
 * them. Firing a whole window at once is what made the list worse rather than
 * better: the requests for rows being looked at went out alongside a dozen for
 * rows not reached yet, and all of them came back slower. Rows on screen are
 * never subject to this.
 *
 * Scaled by how many rows a screen holds, because that is how many are
 * consumed per screenful of scrolling: a flat cap that keeps a loose list
 * ahead leaves a dense one, where a screen is twenty rows rather than four,
 * permanently behind.
 */
const SPECULATIVE_IN_FLIGHT_BOUNDS = { min: 3, max: 8 } as const;

export const maxSpeculativeInFlight = (rows: number): number =>
    Math.min(
        SPECULATIVE_IN_FLIGHT_BOUNDS.max,
        Math.max(SPECULATIVE_IN_FLIGHT_BOUNDS.min, Math.ceil(rows / 3)),
    );

export interface VisibleRange {
    startIndex: number;
    endIndex: number;
}

export interface PrefetchWindowInput {
    /** The rows genuinely on screen, before overscan. */
    range: VisibleRange | null;
    /** Rows in the list. */
    count: number;
    /** How many rows a screenful holds, at the current spacing. */
    rowsPerViewport: number;
    direction: ScrollDirection;
    /**
     * Whether to speculate at all. False while the list is moving too fast for
     * it to pay, which narrows the window to what is actually on screen.
     */
    includeLead: boolean;
}

/**
 * The rows worth having a preview for, as an inclusive index range.
 *
 * `null` before the list has reported where it is — there is nothing to be
 * ahead of yet.
 */
export const prefetchWindow = ({
    range,
    count,
    rowsPerViewport,
    direction,
    includeLead,
}: PrefetchWindowInput): VisibleRange | null => {
    if (range === null || count <= 0) return null;

    const clamp = (index: number) => Math.min(count - 1, Math.max(0, index));
    if (!includeLead) {
        return {
            startIndex: clamp(range.startIndex),
            endIndex: clamp(range.endIndex),
        };
    }

    const rows = Math.max(1, rowsPerViewport);
    const lead = Math.ceil(LEAD_VIEWPORTS * rows);
    const trail = Math.ceil(TRAIL_VIEWPORTS * rows);
    // `null` reads as forward: down is where a list is read, and the first
    // scroll of a session should already be warm ahead of the user.
    const back = direction === "backward";

    return {
        startIndex: clamp(range.startIndex - (back ? lead : trail)),
        endIndex: clamp(range.endIndex + (back ? trail : lead)),
    };
};

/** How many rows a screenful holds, at the height rows currently have. */
export const rowsPerViewport = (
    viewportHeight: number,
    rowEstimate: number,
): number =>
    rowEstimate > 0 ? Math.max(1, Math.ceil(viewportHeight / rowEstimate)) : 1;

/**
 * How fast the list is moving, in screenfuls a second.
 *
 * `0` when no time has passed, so the first sample of a scroll never reads as
 * infinitely fast and suppresses the speculation it should be starting.
 */
export const scrollViewportsPerSecond = (
    deltaPx: number,
    deltaMs: number,
    viewportHeight: number,
): number => {
    if (deltaMs <= 0 || viewportHeight <= 0) return 0;
    return Math.abs(deltaPx) / viewportHeight / (deltaMs / 1000);
};

export interface PrefetchAdmission {
    /** Whether the row is one the user can already see. */
    onScreen: boolean;
    /** Speculative requests still outstanding. */
    inFlight: number;
    /** From `maxSpeculativeInFlight`, for how dense the list currently is. */
    maxInFlight: number;
}

/**
 * Whether to ask for this row's preview now.
 *
 * A row on screen is never held back — a visible card with nothing in it is
 * the thing this exists to prevent, and it is also the request most worth
 * making. Everything else waits its turn, because the requests all share one
 * API: measured, firing a whole window at once made the list worse than not
 * prefetching at all.
 */
export const admitForPrefetch = ({
    onScreen,
    inFlight,
    maxInFlight,
}: PrefetchAdmission): boolean => onScreen || inFlight < maxInFlight;

/**
 * Rows either side of the highlight whose thumbnail is warmed regardless.
 *
 * When thumbnails are off, the highlighted card is the only one that shows
 * one — so the image is first asked for at the moment of highlighting, and
 * measured, arrives 150-330ms later. Walking the list with the arrow keys
 * says where the highlight is going, which is enough to have it already.
 */
export const THUMBNAIL_NEIGHBOURS = 2;

export interface ThumbnailWarmInput {
    /** The rows worth having a preview for. */
    window: VisibleRange | null;
    /** Where the highlight is, or -1. */
    highlightedIndex: number;
    /** Whether every card shows a thumbnail, or only the highlighted one. */
    thumbnailsShownOnEveryCard: boolean;
    count: number;
}

/**
 * Which rows' thumbnail images are worth fetching ahead of being shown.
 *
 * With thumbnails on every card, that is the prefetch window: the image is
 * part of the card the user is scrolling towards. With them off, the window
 * is irrelevant — none of those cards will draw one — and the only rows that
 * will are the ones the highlight is about to reach.
 */
export const thumbnailWarmRange = ({
    window,
    highlightedIndex,
    thumbnailsShownOnEveryCard,
    count,
}: ThumbnailWarmInput): VisibleRange | null => {
    if (count <= 0) return null;
    if (thumbnailsShownOnEveryCard) return window;
    if (highlightedIndex < 0) return null;
    return {
        startIndex: Math.max(0, highlightedIndex - THUMBNAIL_NEIGHBOURS),
        endIndex: Math.min(count - 1, highlightedIndex + THUMBNAIL_NEIGHBOURS),
    };
};
