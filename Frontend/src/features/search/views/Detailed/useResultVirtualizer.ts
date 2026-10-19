import {
    defaultRangeExtractor,
    observeElementRect,
    Range,
    useVirtualizer,
    Virtualizer,
} from "@tanstack/react-virtual";
import {
    RefObject,
    useCallback,
    useLayoutEffect,
    useRef,
    useState,
} from "react";

import { NamedDensity } from "@app/slices/searchSlice";

import { SCROLL_PADDING_PX } from "./highlightScroll";
import { ScrollDirection, scrollViewportsPerSecond } from "./resultPrefetch";

/**
 * Rows kept rendered either side of the viewport.
 *
 * Four rather than one or two for a reason beyond smooth scrolling: the cards'
 * IntersectionObservers have to report a card out of view *before* it is
 * unmounted, or the in-view bookkeeping is left to the unmount cleanup. A
 * margin of a few rows keeps the observer the primary path.
 */
const OVERSCAN = 4;

/**
 * Starting guess at a row's height, per spacing.
 *
 * These are estimates, not measurements: they only ever apply to rows that
 * have not been rendered yet, and every row is measured for real the first
 * time it comes into view. Worth re-deriving from the median of
 * `virtualizer.measurementsCache` against a real corpus if the scrollbar
 * moves noticeably while scrolling.
 *
 * Guess high rather than low. A row placed at a larger offset than it needs
 * leaves a gap that closes as it is measured; one placed at a smaller offset
 * is drawn over its neighbour until then. Tighter spacing trims padding and
 * line height — it removes no fields — so even the tightest card is nowhere
 * near as short as an empty one, which is what these used to assume.
 */
const DENSITY_ROW_ESTIMATE: Record<NamedDensity | "custom", number> = {
    compact: 180,
    standard: 260,
    full: 400,
    custom: 260,
};

/**
 * The line layout draws one line of fields whatever the spacing says, so it is
 * a different order of height from the stacked layouts and cannot be
 * estimated from the density alone.
 */
const LINE_ROW_ESTIMATE: Record<NamedDensity | "custom", number> = {
    compact: 40,
    standard: 56,
    full: 72,
    custom: 56,
};

/**
 * Rows the estimate is derived from before it stops being refined.
 *
 * A screenful or two already settles it, and the cap is what keeps the sort
 * below cheap enough to run from the virtualizer's change callback.
 */
const ESTIMATE_SAMPLE_CAP = 256;

/** Which measured row the estimate is taken from, once they are in order. */
const ESTIMATE_QUANTILE = 0.8;

/**
 * A row height to place unmeasured rows at, from the rows measured so far.
 *
 * A quantile rather than the mean, to keep the bias the constants above are
 * written with: a row placed further down than it needs leaves a gap that
 * closes the moment it is measured, while one placed too close is drawn over
 * its neighbour until then. `fallback` stands in until something is measured —
 * the constants are only ever a first guess, and a corpus of short mails and
 * one of scanned reports do not have the same rows at all.
 */
export const estimateFromMeasured = (
    sizes: Iterable<number>,
    fallback: number,
    cap: number,
): number => {
    const sample: number[] = [];
    for (const size of sizes) {
        sample.push(size);
        if (sample.length >= cap) break;
    }
    if (sample.length === 0) return fallback;
    sample.sort((a, b) => a - b);
    const at = Math.min(
        sample.length - 1,
        Math.floor(sample.length * ESTIMATE_QUANTILE),
    );
    return Math.round(sample[at]);
};

export interface ResultVirtualizerOptions {
    /** One entry per card, in rendered order. */
    orderedFileIds: string[];
    /** Index that must stay rendered however far it is scrolled away. */
    stickyIndex: number | null;
    density: NamedDensity | "custom";
    /** True while the fields are drawn as one line per card. */
    lineLayout: boolean;
    /**
     * Changes whenever anything that decides a row's height changes.
     *
     * Every measured height is cached against the row it was taken from, so a
     * settings change that makes the cards taller or shorter leaves the whole
     * cache describing a layout that is gone — rows get placed at offsets
     * computed from heights they no longer have, and they overlap. The cache
     * is thrown away whenever this changes, so this has to account for
     * everything that resizes a card: the spacing, the field layout, the row
     * chrome, which fields are shown and how wide their columns are.
     */
    layoutSignature: string;
    scrollRef: RefObject<HTMLDivElement | null>;
    /** The element the rows are laid out in, inside the scroller. */
    listRef: RefObject<HTMLDivElement | null>;
    /** False while the panel is hidden and measures zero. */
    isActive: boolean;
}

export type ResultVirtualizer = Virtualizer<HTMLDivElement, HTMLDivElement>;

/** How the list is moving, for callers deciding whether to speculate. */
export interface ScrollMotion {
    direction: ScrollDirection;
    /** Screenfuls a second, which is what "fast" means to the reader. */
    viewportsPerSecond: number;
}

export interface ResultVirtualizerHandle {
    virtualizer: ResultVirtualizer;
    /** Discard every cached height and take them again. */
    remeasure: () => void;
    /**
     * How the list is moving, right now.
     *
     * A getter reading a ref rather than state: it changes on every scroll
     * frame, and re-rendering the list for it would cost more than it saves.
     */
    getMotion: () => ScrollMotion;
}

/**
 * Only report a scroller that actually has a size.
 *
 * The search panel stays mounted and is hidden with `display: none`, which
 * leaves it with no layout box: every rect reads zero. Taken at face value
 * that collapses the rendered range to a single row and unmounts the list, so
 * returning to the tab would rebuild it from nothing. Holding the last real
 * height instead means the window survives the round trip.
 */
const observeNonZeroRect: typeof observeElementRect = (instance, cb) =>
    observeElementRect(instance, (rect) => {
        if (rect.height === 0 && rect.width === 0) return;
        cb(rect);
    });

export const useResultVirtualizer = ({
    orderedFileIds,
    stickyIndex,
    density,
    lineLayout,
    layoutSignature,
    scrollRef,
    listRef,
    isActive,
}: ResultVirtualizerOptions): ResultVirtualizerHandle => {
    // Read inside callbacks the virtualizer holds onto, so they must not go
    // stale and must not change the callbacks' identity.
    const orderedFileIdsRef = useRef(orderedFileIds);
    orderedFileIdsRef.current = orderedFileIds;
    const stickyIndexRef = useRef(stickyIndex);
    stickyIndexRef.current = stickyIndex;
    const rowEstimate = lineLayout
        ? LINE_ROW_ESTIMATE[density]
        : DENSITY_ROW_ESTIMATE[density];
    const estimateRef = useRef(rowEstimate);
    // The constant the estimate starts from, for the callback below, which the
    // virtualizer holds onto and which must not close over a stale one.
    const rowEstimateRef = useRef(rowEstimate);
    rowEstimateRef.current = rowEstimate;
    // How many rows the estimate in hand was derived from. Also the guard
    // against re-deriving it on every notification: the measured heights are
    // only worth another look once there are more of them.
    const sampledRowsRef = useRef(0);

    // Distance from the top of the scrollable content to the top of the list:
    // the container's own padding, plus the column header when the layout
    // shows one. State rather than a ref, because the virtualizer takes it as
    // an option and so has to be handed a new one when it moves. Seeded with
    // the container padding so the first frame does not jump.
    const [scrollMargin, setScrollMargin] = useState(16);

    const getScrollElement = useCallback(() => scrollRef.current, [scrollRef]);
    const estimateSize = useCallback(() => estimateRef.current, []);
    const getItemKey = useCallback(
        (index: number) => orderedFileIdsRef.current[index] ?? index,
        [],
    );

    // The highlighted card is found through the DOM by about a dozen keyboard
    // shortcuts — the action hotkeys click a button inside it — so it has to
    // stay rendered even when it is nowhere near the viewport. Without this
    // they fail silently the moment the user scrolls away from the highlight.
    const rangeExtractor = useCallback((range: Range) => {
        const visible = defaultRangeExtractor(range);
        const sticky = stickyIndexRef.current;
        if (sticky === null || visible.includes(sticky)) return visible;
        return [...visible, sticky].sort((a, b) => a - b);
    }, []);

    // Rows that have not been rendered yet are placed at the estimate, and the
    // further the list is jumped the more of them stand between the scroll
    // position and the card being scrolled to. Feeding the heights already
    // taken back into the guess is what keeps that error small enough for the
    // placement to converge in a frame or two rather than visibly hunting.
    const refreshEstimate = useCallback((instance: ResultVirtualizer) => {
        const measured = instance.itemSizeCache;
        if (measured.size === sampledRowsRef.current) return;
        if (sampledRowsRef.current >= ESTIMATE_SAMPLE_CAP) return;
        sampledRowsRef.current = measured.size;
        estimateRef.current = estimateFromMeasured(
            measured.values(),
            rowEstimateRef.current,
            ESTIMATE_SAMPLE_CAP,
        );
    }, []);

    // How the list is moving. Kept in refs and read through a getter: this
    // changes on every scroll frame, and putting it in state would re-render
    // the whole list for something only the prefetcher asks about.
    const motionRef = useRef<ScrollMotion>({
        direction: null,
        viewportsPerSecond: 0,
    });
    const lastOffsetRef = useRef<number | null>(null);
    const lastSampleAtRef = useRef(0);

    const trackMotion = useCallback((instance: ResultVirtualizer) => {
        const offset = instance.scrollOffset;
        const now = performance.now();
        const previous = lastOffsetRef.current;
        if (offset !== null && previous !== null) {
            motionRef.current = {
                direction: instance.scrollDirection,
                viewportsPerSecond: scrollViewportsPerSecond(
                    offset - previous,
                    now - lastSampleAtRef.current,
                    instance.scrollRect?.height ?? 0,
                ),
            };
        }
        lastOffsetRef.current = offset;
        lastSampleAtRef.current = now;
        // Standing still is not slow scrolling: without this the last speed
        // measured would persist and keep speculation switched off.
        if (
            !instance.isScrolling &&
            motionRef.current.viewportsPerSecond !== 0
        ) {
            motionRef.current = {
                direction: motionRef.current.direction,
                viewportsPerSecond: 0,
            };
        }
    }, []);

    const handleChange = useCallback(
        (instance: ResultVirtualizer) => {
            refreshEstimate(instance);
            trackMotion(instance);
        },
        [refreshEstimate, trackMotion],
    );

    const getMotion = useCallback(() => motionRef.current, []);

    const virtualizer = useVirtualizer<HTMLDivElement, HTMLDivElement>({
        count: orderedFileIds.length,
        getScrollElement,
        estimateSize,
        getItemKey,
        rangeExtractor,
        observeElementRect: observeNonZeroRect,
        overscan: OVERSCAN,
        scrollMargin,
        // The band the highlighted card is kept inside. `scrollToIndex` aligns
        // to these, so a card is never placed flush against an edge.
        scrollPaddingStart: SCROLL_PADDING_PX,
        scrollPaddingEnd: SCROLL_PADDING_PX,
        onChange: handleChange,
    });

    const measureScrollMargin = useCallback(() => {
        const list = listRef.current;
        const scroller = scrollRef.current;
        if (!list || !scroller) return;
        const margin =
            list.getBoundingClientRect().top -
            scroller.getBoundingClientRect().top +
            scroller.scrollTop;
        // Guarded: this runs from layout effects that the virtualizer's own
        // notifications re-trigger, and setting an unchanged value would loop.
        setScrollMargin((current) =>
            Math.abs(current - margin) < 1 ? current : margin,
        );
    }, [listRef, scrollRef]);

    /**
     * Throw away every cached height and take them again.
     *
     * The two halves belong together. `measure()` only empties the cache, and
     * React hands an element to `measureElement` solely when it mounts — so
     * the rows already on screen would be left at the estimate while
     * rendering at their real height, drawn over each other until their
     * ResizeObserver reported, a frame or more later. Clearing without
     * refilling is what made the cards overlap.
     */
    const remeasure = useCallback(() => {
        virtualizer.measure();
        // The heights the estimate was derived from have just been thrown
        // away with the rest, so it goes back to being derived from scratch —
        // including when it had already settled on its sample cap.
        sampledRowsRef.current = 0;
        const list = listRef.current;
        if (!list) return;
        // In a microtask rather than here. Reporting a height makes the
        // virtualizer notify, and its React adapter answers a synchronous
        // notification with `flushSync` — which React refuses from inside the
        // commit this runs in, and says so. A microtask runs once the commit
        // has finished and still before the browser paints, so the rows are
        // placed correctly on the first frame either way.
        queueMicrotask(() => {
            if (!listRef.current) return;
            // Rebuild the offsets before reporting into them: a report is
            // compared against them, and against the discarded layout it
            // would read as no change and be dropped.
            virtualizer.getVirtualItems();
            for (const row of listRef.current.querySelectorAll<HTMLElement>(
                "[data-index]",
            )) {
                const index = Number(row.dataset.index);
                if (Number.isNaN(index)) continue;
                // Reported through `resizeItem` rather than `measureElement`,
                // which declines to measure while the list is scrolling.
                virtualizer.resizeItem(index, row.offsetHeight);
            }
        });
    }, [listRef, virtualizer]);

    // Coming back to the tab: the panel had no layout box while hidden, so the
    // offsets measured before it was hidden are the ones still in hand. They
    // are usually right, but a resize while away would have gone unseen.
    useLayoutEffect(() => {
        if (!isActive) return;
        measureScrollMargin();
        remeasure();
    }, [isActive, measureScrollMargin, remeasure]);

    // Every cached height describes the layout it was taken under, so a
    // settings change invalidates all of them at once.
    useLayoutEffect(() => {
        estimateRef.current = rowEstimate;
        // The same settings also move the list itself — a column header
        // appears, the container's padding changes — so where it starts has
        // to be re-read along with how tall its rows are.
        measureScrollMargin();
        remeasure();
    }, [layoutSignature, rowEstimate, measureScrollMargin, remeasure]);

    return { virtualizer, remeasure, getMotion };
};
