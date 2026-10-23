import { RefObject, useEffect, useRef } from "react";

import { useAppDispatch } from "@app/hooks";
import { ensureViewPreview } from "@app/slices/searchSlice";
import { webApiGetFileThumbnail } from "@features/common/urls";

import {
    admitForPrefetch,
    MAX_PREFETCH_VIEWPORTS_PER_SECOND,
    maxSpeculativeInFlight,
    prefetchWindow,
    rowsPerViewport,
    thumbnailWarmRange,
    VisibleRange,
} from "./resultPrefetch";
import { ScrollMotion } from "./useResultVirtualizer";

export interface ResultPrefetchOptions {
    /** One entry per row, in rendered order. */
    orderedFileIds: string[];
    /** The rows genuinely on screen, before overscan. */
    range: VisibleRange | null;
    /** How tall a row currently is, measured or estimated. */
    rowEstimate: number;
    scrollRef: RefObject<HTMLDivElement | null>;
    getMotion: () => ScrollMotion;
    /** Thumbnail id per row, for the ones whose preview is already cached. */
    thumbnailIdFor: (fileId: string) => string | undefined;
    /** Where the highlight is, or -1. */
    highlightedIndex: number;
    /** False when only the highlighted card draws a thumbnail. */
    thumbnailsShownOnEveryCard: boolean;
    /** Counts the queries that have replaced the list; see the reset below. */
    resultsReplaced: number;
}

/**
 * Fetch previews for the rows the user is about to reach.
 *
 * A card renders complete the moment its preview is in the store and falls
 * back to a skeleton only when the cache is cold, so having the data in hand
 * is enough — the row does not also have to be mounted early. That is why this
 * works from the virtual range rather than from an observer on each card: an
 * observer cannot report a row that is not mounted, so it could never reach
 * further than the overscan, and it would cost one more IntersectionObserver
 * on every card.
 *
 * `ensureViewPreview` is guarded by `isPreviewFresh`, so asking twice for a
 * row already in hand costs nothing and the duplicates dedupe themselves.
 */
export const useResultPrefetch = ({
    orderedFileIds,
    range,
    rowEstimate,
    scrollRef,
    getMotion,
    thumbnailIdFor,
    highlightedIndex,
    thumbnailsShownOnEveryCard,
    resultsReplaced,
}: ResultPrefetchOptions) => {
    const dispatch = useAppDispatch();
    // Which rows a request actually went out for.
    //
    // `ensureViewPreview` only skips rows whose preview is already cached, and
    // a request in flight has not cached anything yet — so without this, every
    // row scrolled by re-asked for the whole window and the duplicates queued
    // ahead of the rows actually on screen. Measured: it made the list worse,
    // not better.
    //
    // A row whose dispatch was *skipped* is deliberately not recorded. It used
    // to be, which turned this from a record of what had been asked into a
    // promise never to ask: a card holding a fresh preview was marked here,
    // and when the preview was later thrown away the row was never fetched
    // again, so it sat as a skeleton for as long as the result set lasted.
    const requestedRef = useRef(new Set<string>());
    // A new query resets the list; a new page only ever grows it and keeps the
    // row it starts with. Only the former is a reason to ask again.
    const listShapeRef = useRef({ first: "", length: 0, replaced: -1 });
    // Speculative requests still out. Rows on screen do not count against it.
    const inFlightRef = useRef(0);
    // Thumbnail URLs already handed to the browser. The cache serves the real
    // `<img>` when it mounts, so this only has to happen once per image.
    const warmedRef = useRef(new Set<string>());

    const startIndex = range?.startIndex ?? null;
    const endIndex = range?.endIndex ?? null;

    useEffect(() => {
        if (startIndex === null || endIndex === null) return;
        const viewportHeight = scrollRef.current?.clientHeight ?? 0;
        if (viewportHeight === 0) return;

        const first = orderedFileIds[0] ?? "";
        const shape = listShapeRef.current;
        // `resultsReplaced` counts every query that replaced the list, which
        // the first row's id cannot: the same search asked again returns the
        // same rows in the same order, so nothing here looked new even though
        // every preview behind it had just been discarded.
        if (
            resultsReplaced !== listShapeRef.current.replaced ||
            first !== shape.first ||
            orderedFileIds.length < shape.length
        ) {
            requestedRef.current = new Set();
        }
        listShapeRef.current = {
            first,
            length: orderedFileIds.length,
            replaced: resultsReplaced,
        };

        const motion = getMotion();
        // Above the threshold the rows are gone before a request for them
        // could return, and those requests queue ahead of the ones for the
        // rows the user actually stops on. The window narrows to what is on
        // screen — never below it, because a visible card with nothing in it
        // is the thing this exists to prevent.
        const includeLead =
            motion.viewportsPerSecond <= MAX_PREFETCH_VIEWPORTS_PER_SECOND;

        const rows = rowsPerViewport(viewportHeight, rowEstimate);
        const maxInFlight = maxSpeculativeInFlight(rows);
        const window = prefetchWindow({
            range: { startIndex, endIndex },
            count: orderedFileIds.length,
            rowsPerViewport: rows,
            direction: motion.direction,
            includeLead,
        });
        if (!window) return;

        // On screen first. Requests are served roughly in the order they are
        // made, so asking for the speculative rows first would put them ahead
        // of the ones the user is looking at.
        const order: number[] = [];
        for (let i = startIndex; i <= endIndex; i++) order.push(i);
        for (let i = window.startIndex; i <= window.endIndex; i++) {
            if (i < startIndex || i > endIndex) order.push(i);
        }

        // The thumbnail is a separate request from the preview, and nothing
        // was asking for it until the `<img>` mounted — which, with
        // thumbnails off, is the moment of highlighting. Fetched at low
        // priority so it never gets in front of the previews above.
        const warm = thumbnailWarmRange({
            window,
            highlightedIndex,
            thumbnailsShownOnEveryCard,
            count: orderedFileIds.length,
        });
        if (warm) {
            for (let i = warm.startIndex; i <= warm.endIndex; i++) {
                const fileId = orderedFileIds[i];
                if (fileId === undefined) continue;
                const thumbnailId = thumbnailIdFor(fileId);
                if (thumbnailId === undefined) continue;
                const url = webApiGetFileThumbnail(fileId, thumbnailId);
                if (warmedRef.current.has(url)) continue;
                warmedRef.current.add(url);
                const image = new Image();
                image.fetchPriority = "low";
                image.src = url;
            }
        }

        for (const index of order) {
            const fileId = orderedFileIds[index];
            if (fileId === undefined) continue;
            if (requestedRef.current.has(fileId)) continue;

            const onScreen = index >= startIndex && index <= endIndex;
            if (
                !admitForPrefetch({
                    onScreen,
                    inFlight: inFlightRef.current,
                    maxInFlight,
                })
            ) {
                // Not marked as asked for: the next scroll should pick it up
                // rather than skip it forever.
                continue;
            }

            // Recorded only once the dispatch has been accepted: a row the
            // thunk's condition turned away has not been asked for.
            const remember = (result: { meta?: { condition?: boolean } }) => {
                if (result?.meta?.condition) return;
                requestedRef.current.add(fileId);
            };
            if (onScreen) {
                remember(
                    dispatch(ensureViewPreview({ fileId })) as unknown as {
                        meta?: { condition?: boolean };
                    },
                );
                continue;
            }
            inFlightRef.current += 1;
            const dispatched = dispatch(ensureViewPreview({ fileId }));
            remember(
                dispatched as unknown as { meta?: { condition?: boolean } },
            );
            void Promise.resolve(dispatched)
                .catch(() => {})
                .finally(() => {
                    inFlightRef.current -= 1;
                });
        }
    }, [
        startIndex,
        endIndex,
        orderedFileIds,
        rowEstimate,
        scrollRef,
        getMotion,
        thumbnailIdFor,
        highlightedIndex,
        thumbnailsShownOnEveryCard,
        resultsReplaced,
        dispatch,
    ]);
};
