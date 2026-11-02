import {
    defaultRangeExtractor,
    measureElement,
    observeElementRect,
    Range,
    useVirtualizer,
    Virtualizer,
} from "@tanstack/react-virtual";
import {
    RefObject,
    useCallback,
    useLayoutEffect,
    useReducer,
    useRef,
    useState,
} from "react";

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
 * is drawn over its neighbour until then. A card is laid out tight, which
 * trims padding and line height and removes no fields, so it is nowhere near
 * as short as an empty one.
 */
const STACKED_ROW_ESTIMATE = 180;

/**
 * The line layout draws one line of fields, so it is a different order of
 * height from the stacked layout and cannot take the same starting guess.
 */
const LINE_ROW_ESTIMATE = 40;

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
     * Record one row's height, now.
     *
     * For the moment a row's content changes under it - a skeleton becoming a
     * card when its preview lands, most of all. The ResizeObserver reports
     * that too, but only after the frame it happened in, and until it does the
     * row below is drawn over it.
     */
    recordHeight: (index: number, height: number) => void;
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

/**
 * Refuse a row measurement of zero, and keep the height already in hand.
 *
 * The same `display: none` leaves every *row* without a layout box too, and a
 * hidden row measures 0px. Both of the virtualizer's measurement paths — the
 * ResizeObserver it puts on each row, and the measurement a row takes when it
 * mounts — record that, and a row recorded as nothing tall shrinks the total
 * size, which moves the scroll offset, which renders a different window, whose
 * rows are then measured at zero in their turn. Left unguarded, that runaway
 * walks the result list hundreds of rows away from where the reader left it
 * within seconds, and further the longer the list stays hidden.
 */
export const measureNonZero: typeof measureElement = (
    element,
    entry,
    instance,
) => {
    const size = measureElement(element, entry, instance);
    if (size > 0) return size;
    const index = instance.indexFromElement(element);
    const key = instance.options.getItemKey(index);
    return (
        instance.itemSizeCache.get(key) ?? instance.options.estimateSize(index)
    );
};

export const useResultVirtualizer = ({
    orderedFileIds,
    stickyIndex,
    lineLayout,
    layoutSignature,
    scrollRef,
    listRef,
}: ResultVirtualizerOptions): ResultVirtualizerHandle => {
    // Read inside callbacks the virtualizer holds onto, so they must not go
    // stale and must not change the callbacks' identity.
    const orderedFileIdsRef = useRef(orderedFileIds);
    orderedFileIdsRef.current = orderedFileIds;
    const stickyIndexRef = useRef(stickyIndex);
    stickyIndexRef.current = stickyIndex;
    const rowEstimate = lineLayout ? LINE_ROW_ESTIMATE : STACKED_ROW_ESTIMATE;
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

    /**
     * Re-render the list after a row's height changed.
     *
     * The virtualizer records the new height and says so, but while the list
     * is being scrolled its React adapter can leave the rows standing at the
     * offsets of the previous render for a tenth of a second - long enough to
     * watch one card sit on top of the next even though the measurement it is
     * placed from is already right. Coalesced into a microtask so a sweep over
     * every rendered row costs one render, not one per row.
     */
    const [, bumpRows] = useReducer((count: number) => count + 1, 0);
    const redrawQueuedRef = useRef(false);
    const redrawRows = useCallback(() => {
        if (redrawQueuedRef.current) return;
        redrawQueuedRef.current = true;
        queueMicrotask(() => {
            redrawQueuedRef.current = false;
            bumpRows();
        });
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
        measureElement: measureNonZero,
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
     * Record a row's height so it survives the estimate moving afterwards.
     *
     * `resizeItem` treats a report that matches the size the row is currently
     * laid out at as a no-op, and after `measure()` that size *is* the
     * estimate — so a row whose real height happens to equal the estimate
     * never reaches the cache at all. It goes on following the estimate, and
     * the moment the estimate is re-derived from the rows around it, the row
     * is laid out at a height it does not have: a permanent overlap that only
     * a resize of that row can clear. Nudging the report by a pixel first
     * forces the height in.
     */
    const recordHeight = useCallback(
        (index: number, height: number) => {
            const key = virtualizer.options.getItemKey(index);
            const before = virtualizer.itemSizeCache.get(key);
            virtualizer.resizeItem(index, height);
            if (!virtualizer.itemSizeCache.has(key)) {
                virtualizer.resizeItem(index, height + 1);
                virtualizer.resizeItem(index, height);
            }
            if (before !== height) redrawRows();
        },
        [redrawRows, virtualizer],
    );

    /**
     * Take the heights of the rows that are on screen, as they are now.
     *
     * In a microtask rather than inline. Reporting a height makes the
     * virtualizer notify, and its React adapter answers a synchronous
     * notification with `flushSync` — which React refuses from inside the
     * commit a layout effect runs in, and says so. A microtask runs once the
     * commit has finished and still before the browser paints, so the rows are
     * placed correctly on the first frame either way.
     */
    const reportRenderedRows = useCallback(() => {
        if (!listRef.current) return;
        queueMicrotask(() => {
            const list = listRef.current;
            if (!list) return;
            // Rebuild the offsets before reporting into them: a report is
            // compared against them, and against a discarded layout it would
            // read as no change and be dropped.
            virtualizer.getVirtualItems();
            for (const row of list.querySelectorAll<HTMLElement>(
                "[data-index]",
            )) {
                const index = Number(row.dataset.index);
                if (Number.isNaN(index)) continue;
                // A row React has taken out of the document between the commit
                // and this microtask measures zero. Recording that would
                // collapse the row to nothing, lift everything below it, and
                // drag the estimate down with it.
                if (!row.isConnected) continue;
                const height = row.offsetHeight;
                if (height === 0) continue;
                // Reported through `resizeItem` rather than `measureElement`,
                // which declines to measure while the list is scrolling.
                recordHeight(index, height);
            }
        });
    }, [listRef, recordHeight, virtualizer]);

    /**
     * Throw away every cached height and take them again.
     *
     * The two halves belong together. `measure()` only empties the cache, and
     * React hands an element to `measureElement` solely when it mounts — so
     * the rows already on screen would be left at the estimate while
     * rendering at their real height, drawn over each other until their
     * ResizeObserver reported, a frame or more later.
     */
    const remeasure = useCallback(() => {
        virtualizer.measure();
        // The heights the estimate was derived from have just been thrown
        // away with the rest, so it goes back to being derived from scratch —
        // including when it had already settled on its sample cap.
        sampledRowsRef.current = 0;
        reportRenderedRows();
    }, [reportRenderedRows, virtualizer]);

    // The scroll margin and the rows on screen are measured once the list has
    // one, which is the first layout after mount.
    useLayoutEffect(() => {
        measureScrollMargin();
        reportRenderedRows();
    }, [measureScrollMargin, reportRenderedRows]);

    // Every cached height describes the layout it was taken under, so a
    // settings change invalidates all of them at once.
    //
    // The reader's place is held by the row at the top of the viewport, not by
    // the pixel offset: every row is about to be a different height, so the
    // same offset lands somewhere else entirely. Without the anchor, changing
    // the spacing moves the first visible result by a hundred places.
    const firstLayoutRef = useRef(true);
    useLayoutEffect(() => {
        estimateRef.current = rowEstimate;
        const scroller = scrollRef.current;
        const anchorIndex = virtualizer.range?.startIndex ?? null;
        // Where that row sits on screen right now. Holding it there is exact,
        // where scrolling to its computed offset is only as good as the
        // heights guessed for every row above it.
        const anchorTop =
            anchorIndex === null || !scroller
                ? null
                : (
                      listRef.current?.querySelector<HTMLElement>(
                          `[data-index="${anchorIndex}"]`,
                      ) ?? null
                  )?.getBoundingClientRect().top;
        // The same settings also move the list itself — a column header
        // appears, the container's padding changes — so where it starts has
        // to be re-read along with how tall its rows are.
        measureScrollMargin();
        remeasure();
        if (firstLayoutRef.current) {
            firstLayoutRef.current = false;
            return;
        }
        if (anchorIndex === null || anchorTop == null || !scroller) return;
        // Over several frames, not once: the heights arrive in the microtask
        // below, the rows lay out against them in the frame after that, and
        // rows further down are measured as they are reached. Correcting
        // until the anchor stops moving is what holds it exactly, where a
        // single correction leaves the reader tens of results adrift.
        let framesLeft = 10;
        const hold = () => {
            const row = listRef.current?.querySelector<HTMLElement>(
                `[data-index="${anchorIndex}"]`,
            );
            framesLeft -= 1;
            if (!row) {
                // A spacing change can be large enough that the same scroll
                // offset now lands on an entirely different part of the list,
                // leaving the anchor outside the rendered window. Bring it
                // back into view first, then keep correcting: the next frame
                // will find it and place it exactly.
                virtualizer.scrollToIndex(anchorIndex, { align: "start" });
                if (framesLeft > 0) requestAnimationFrame(hold);
                return;
            }
            const moved = row.getBoundingClientRect().top - anchorTop;
            if (Math.abs(moved) > 0.5) scroller.scrollTop += moved;
            if (framesLeft > 0) requestAnimationFrame(hold);
        };
        queueMicrotask(() => queueMicrotask(hold));
    }, [
        layoutSignature,
        rowEstimate,
        listRef,
        measureScrollMargin,
        remeasure,
        scrollRef,
        virtualizer,
    ]);

    return { virtualizer, remeasure, recordHeight, getMotion };
};
