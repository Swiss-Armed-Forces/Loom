import React, {
    CSSProperties,
    ReactNode,
    useCallback,
    useContext,
    useEffect,
    useLayoutEffect,
    useMemo,
    useRef,
} from "react";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectIsLoading } from "@app/slices/commonSlice";
import {
    selectCardElementVisibility,
    selectFieldColumnWidths,
    selectFieldLayout,
    selectPreviewFields,
    selectThumbnailColumnWidth,
    selectHighlightedFileId,
    selectHighlightScrollMode,
    selectHighlightScrollRequest,
    selectIsPaginating,
    selectOrderedFileIds,
    selectQueuedAdvance,
    selectFiles,
    selectResultOrder,
    selectResultsReplaced,
    selectTemporaryFileId,
    visibleRangeChanged,
} from "@app/slices/searchSlice";
import { TourContext } from "@app/tours/TourContext";
import {
    EmptySearchResults,
    LoadMoreButton,
    ResultCard,
} from "@features/search/components";
import { FieldColumnHeader } from "@features/search/components/FieldList/FieldColumnHeader";
import {
    COLUMN_HOST_ATTR,
    FIELD_COLUMNS_VAR,
    cardThumbnailStyle,
    columnWidthsOf,
    fieldColumnTemplate,
    reservesThumbnailSlot,
    thumbnailSlotStyle,
} from "@features/search/components/FieldList/fieldColumns";
import { ResultCardSkeleton } from "@features/search/components/ResultCard/ResultCardSkeleton";
import { rowRhythmStyle } from "@features/search/components/ResultCard/rowRhythm";
import { useSearchPanel } from "@features/search/views/SearchResults/SearchPanelContext";

import styles from "./DetailedView.module.css";
import { alignForHighlight, HighlightScrollMode } from "./highlightScroll";
import { useResultPrefetch } from "./useResultPrefetch";
import { useResultVirtualizer } from "./useResultVirtualizer";

// Placed by the browser rather than by the virtualizer: the pending page row
// is a plain element below the virtual list, not a row the virtualizer knows
// about. `nearest` is the same rule as the virtualizer's `auto` — leave a row
// that is already in view alone, and align the start edge of one too tall to
// fit — and it honours the scroller's `scroll-padding`, which is where the
// same gap the virtualizer is given is written for this path.
const scrollPendingRowIntoView = (
    container: HTMLDivElement,
    mode: HighlightScrollMode,
) => {
    const row = container.querySelector(
        '[data-highlighted="true"]',
    ) as HTMLElement | null;
    row?.scrollIntoView({ block: mode === "top" ? "start" : "nearest" });
};

interface ResultRowProps {
    index: number;
    measureElement: (node: HTMLDivElement | null) => void;
    recordHeight: (index: number, height: number) => void;
    /** False while the card is still drawing a skeleton. */
    hasPreview: boolean;
    /** True for the card the keyboard is on, which draws every element. */
    isHighlighted: boolean;
    children: ReactNode;
}

/**
 * One row of the result list.
 *
 * Rows sit in normal flow inside the window below, rather than each being
 * placed at an offset of its own. That is what makes a card drawn over its
 * neighbour impossible: a row that grows pushes the rows after it down in the
 * same layout pass, where a row placed at a remembered offset stayed where it
 * was until the measurement caught up a frame or more later.
 *
 * The layout effect still reports the new height, because the virtualizer
 * needs it for the rows it has *not* rendered - the scrollbar and the offset
 * the window starts at are computed from the measurements, not from the DOM.
 */
const ResultRow = ({
    index,
    measureElement,
    recordHeight,
    hasPreview,
    isHighlighted,
    children,
}: ResultRowProps) => {
    const rowRef = useRef<HTMLDivElement>(null);
    const setRefs = useCallback(
        (node: HTMLDivElement | null) => {
            rowRef.current = node;
            measureElement(node);
        },
        [measureElement],
    );
    // In a microtask, not inline: reporting makes the virtualizer notify, and
    // its React adapter answers with `flushSync`, which React refuses from
    // inside a commit. A microtask still runs before paint.
    const takeHeight = useCallback(() => {
        queueMicrotask(() => {
            const node = rowRef.current;
            if (!node?.isConnected) return;
            const height = node.offsetHeight;
            if (height > 0) recordHeight(index, height);
        });
    }, [index, recordHeight]);
    useLayoutEffect(takeHeight, [hasPreview, isHighlighted, takeHeight]);
    return (
        <div
            className={styles.resultRow}
            data-index={index}
            // The zebra stripe of the flat chrome is keyed on this rather than
            // on nth-child: only a window of rows is rendered, so sibling
            // position says where the window starts, not where the result is.
            data-stripe={index % 2 === 1 ? "true" : undefined}
            ref={setRefs}
        >
            {children}
        </div>
    );
};

export const DetailedView: React.FC = React.memo(() => {
    const dispatch = useAppDispatch();
    const isLoading = useAppSelector(selectIsLoading);
    const highlightedFileId = useAppSelector(selectHighlightedFileId);
    const highlightScrollRequest = useAppSelector(selectHighlightScrollRequest);
    const highlightScrollMode = useAppSelector(selectHighlightScrollMode);
    const temporaryFileId = useAppSelector(selectTemporaryFileId);
    const resultOrder = useAppSelector(selectResultOrder);
    const files = useAppSelector(selectFiles);
    const fieldLayout = useAppSelector(selectFieldLayout);
    const previewFields = useAppSelector(selectPreviewFields);
    const columnWidths = useAppSelector(selectFieldColumnWidths);
    const thumbnailWidth = useAppSelector(selectThumbnailColumnWidth);
    const visibility = useAppSelector(selectCardElementVisibility);
    const orderedFileIds = useAppSelector(selectOrderedFileIds);
    const resultsReplaced = useAppSelector(selectResultsReplaced);
    const isPaginating = useAppSelector(selectIsPaginating);
    const queuedAdvance = useAppSelector(selectQueuedAdvance);
    const containerRef = useRef<HTMLDivElement>(null);
    const listRef = useRef<HTMLDivElement>(null);
    const panel = useSearchPanel();
    // Read once, here, and handed down as a boolean. Subscribing to the tour
    // from inside ResultCard would re-render every mounted card on every step.
    // Read straight off the context rather than through useTour, which throws
    // without a provider: the result list does not need a tour to render.
    const tour = useContext(TourContext);
    const activeTourStepId = tour?.activeTourStepId ?? null;
    const tourDetailFileId = tour?.tourDetailFileId ?? null;
    // Stands in when the view is rendered outside the panel, e.g. in a test.
    // A ref rather than a fresh object per render: the virtualizer holds on to
    // the one it was given.
    const detachedScrollRef = useRef<HTMLDivElement>(null);
    const scrollRef = panel?.scrollRef ?? detachedScrollRef;

    // Moves that ran past the last card are waiting on a page: the pending row
    // below takes the highlight so the keypress has something to show for
    // itself, and the card keeps its own highlight off until the page lands —
    // two elements carrying `data-highlighted` would leave the scroll helper
    // chasing the wrong one.
    const highlightPendingRow = queuedAdvance > 0;

    const highlightedIndex =
        highlightedFileId !== null && !highlightPendingRow
            ? orderedFileIds.indexOf(highlightedFileId)
            : -1;

    // One card carries the tour's card steps, so they all describe the same
    // result instead of each finding the first card in the document that
    // happens to have the element they point at.
    const tourAnchorFileId = tourDetailFileId ?? orderedFileIds[0] ?? null;
    const onACardStep = activeTourStepId?.startsWith("result-card") ?? false;

    // During a card step the anchor has to stay rendered for driver.js to
    // find and highlight it, even if the user left it far up the list.
    const tourAnchorIndex =
        onACardStep && tourAnchorFileId !== null
            ? orderedFileIds.indexOf(tourAnchorFileId)
            : -1;
    const stickyIndex =
        tourAnchorIndex !== -1 ? tourAnchorIndex : highlightedIndex;

    // The columns, the row rhythm and the thumbnail slot are published once
    // for the whole list, so the header and every card resolve to the same
    // tracks, the same spacing and the same width kept free on the right.
    const showColumns = fieldLayout === "line";
    const listStyle = useMemo(
        () =>
            ({
                [FIELD_COLUMNS_VAR]: fieldColumnTemplate(
                    columnWidthsOf(previewFields, columnWidths),
                ),
                ...rowRhythmStyle(),
                ...thumbnailSlotStyle(
                    visibility.thumbnailWidthRem,
                    reservesThumbnailSlot(fieldLayout, visibility),
                    thumbnailWidth,
                ),
                ...cardThumbnailStyle(visibility.thumbnailWidthRem),
            }) as CSSProperties,
        [previewFields, columnWidths, fieldLayout, visibility, thumbnailWidth],
    );

    // Everything that decides how tall a card is, in one string. The
    // virtualizer caches a measured height per row, so any of these changing
    // while results are on screen leaves the whole cache describing a layout
    // that no longer exists — rows land at offsets computed from heights they
    // have not had since, and they overlap. Add to this whenever a new
    // setting can resize a card.
    const layoutSignature = useMemo(
        () =>
            JSON.stringify([
                fieldLayout,
                previewFields,
                columnWidths,
                thumbnailWidth,
                visibility,
            ]),
        [fieldLayout, previewFields, columnWidths, thumbnailWidth, visibility],
    );

    // Called above the empty-list early return: hooks cannot be conditional,
    // and a count of zero costs nothing.
    const { virtualizer, remeasure, recordHeight, getMotion } =
        useResultVirtualizer({
            orderedFileIds,
            stickyIndex: stickyIndex === -1 ? null : stickyIndex,
            lineLayout: fieldLayout === "line",
            layoutSignature,
            scrollRef,
            listRef,
            // The centre column is the result list and only that, so it is
            // never hidden and never measures zero.
        });

    // Re-measure when the container's width changes, since that rewraps
    // every card.
    //
    // Width only. The container's *height* follows from how tall the rows
    // are, so treating that as a reason to re-measure is circular: measuring
    // changes the height, which asks to measure again.
    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        let debounce: ReturnType<typeof setTimeout> | null = null;
        let lastWidth = el.getBoundingClientRect().width;
        const ro = new ResizeObserver(([entry]) => {
            const width = entry.contentRect.width;
            // A width of zero is a container with no layout box - before
            // first layout, or inside a collapsed ancestor - and not a
            // window the reader has narrowed. Re-measuring then places the
            // highlight against heights of zero.
            if (width === 0) return;
            if (width === lastWidth) return;
            lastWidth = width;
            if (debounce) clearTimeout(debounce);
            debounce = setTimeout(remeasure, 100);
        });
        ro.observe(el);
        return () => {
            ro.disconnect();
            if (debounce) clearTimeout(debounce);
        };
    }, [remeasure]);

    // Report which rows are on screen, for the search box's position readout.
    // `range` is the genuinely visible rows, before overscan and before the
    // sticky highlight is added back in. This component already re-renders on
    // every scroll — that is what windowing is — so the only cost here is a
    // dispatch, and only when the range actually moves.
    const visibleStart = virtualizer.range?.startIndex ?? null;
    const visibleEnd = virtualizer.range?.endIndex ?? null;
    useEffect(() => {
        dispatch(
            visibleRangeChanged(
                visibleStart === null || visibleEnd === null
                    ? null
                    : { startIndex: visibleStart, endIndex: visibleEnd },
            ),
        );
    }, [visibleStart, visibleEnd, dispatch]);

    // Reads the thumbnail id out of the cache the previews land in. A
    // callback rather than the map itself, so the prefetch does not re-run
    // every time any file in it changes.
    const filesRef = useRef(files);
    filesRef.current = files;
    const thumbnailIdFor = useCallback(
        (fileId: string) => filesRef.current[fileId]?.preview?.thumbnailFileId,
        [],
    );

    // Have the previews for the rows just beyond the fold already in hand, so
    // scrolling onto them shows a card rather than a skeleton.
    useResultPrefetch({
        orderedFileIds,
        range:
            visibleStart === null || visibleEnd === null
                ? null
                : { startIndex: visibleStart, endIndex: visibleEnd },
        rowEstimate: virtualizer.options.estimateSize(0),
        scrollRef,
        getMotion,
        thumbnailIdFor,
        highlightedIndex,
        thumbnailsShownOnEveryCard: visibility.thumbnailWidthRem > 0,
        resultsReplaced,
    });

    const placeHighlight = useCallback(() => {
        const scrollContainer = scrollRef.current;
        if (!scrollContainer) return;
        if (highlightPendingRow) {
            if (containerRef.current) {
                scrollPendingRowIntoView(
                    containerRef.current,
                    highlightScrollMode,
                );
            }
            return;
        }
        if (highlightedIndex === -1) return;
        // Through the virtualizer rather than by setting scrollTop here,
        // because where the row ends up is not known yet: the card being
        // scrolled to is routinely not rendered, so its height is an estimate,
        // and so is every unrendered row between here and there. The
        // virtualizer keeps re-resolving the offset as those rows are measured
        // for real, until it has been stable for a couple of frames — which a
        // position written once cannot do, least of all under a held arrow key
        // that replaces it before the measurements land.
        const item = virtualizer.measurementsCache[highlightedIndex];
        if (!item) return;
        virtualizer.scrollToIndex(highlightedIndex, {
            align: alignForHighlight(
                item.size,
                scrollContainer.clientHeight,
                highlightScrollMode,
            ),
        });
    }, [
        highlightedIndex,
        highlightPendingRow,
        highlightScrollMode,
        scrollRef,
        virtualizer,
    ]);

    // driver.js highlights by bounding rect, so the anchor has to be rendered
    // before the step resolves. The steps carry a waitForElementMs to cover
    // the frame or two this takes.
    useLayoutEffect(() => {
        if (tourAnchorIndex === -1) return;
        virtualizer.scrollToIndex(tourAnchorIndex, { align: "start" });
    }, [tourAnchorIndex, virtualizer]);

    // The user taking the scroll ends the placement, the way the virtualizer's
    // own scroll commands stand down on a scroll they did not write: a card
    // that grows after the user has scrolled away from it must not pull them
    // back to it. Plain scroll events cannot say this, because the correction
    // below is itself a scroll; these are the events only a user produces.
    const userTookOverRef = useRef(false);
    useEffect(() => {
        const scroller = scrollRef.current;
        if (!scroller) return;
        const takeOver = () => {
            userTookOverRef.current = true;
        };
        const events = ["wheel", "touchmove", "mousedown"] as const;
        for (const event of events) {
            scroller.addEventListener(event, takeOver, { passive: true });
        }
        return () => {
            for (const event of events) {
                scroller.removeEventListener(event, takeOver);
            }
        };
    }, [scrollRef]);

    // A query that replaces the list puts its first page on screen, so the
    // reader goes back to the top of it. Without this the scroll position was
    // carried over from the previous result set and the new one opened
    // part-way in, with its best matches above the fold.
    const firstResultsRef = useRef(true);
    useLayoutEffect(() => {
        if (firstResultsRef.current) {
            firstResultsRef.current = false;
            return;
        }
        const scroller = scrollRef.current;
        if (scroller) scroller.scrollTop = 0;
        // Through the virtualizer as well as the element: it keeps its own
        // idea of where the list is scrolled to and will write it back over a
        // position set behind it.
        virtualizer.scrollToOffset(0);
        // A highlight left over from the previous query still names a file,
        // and if that file happens to be in the new results too, the
        // correcting placement below would pull the view straight back down to
        // it. Going to the top of a new result set is the reader's position
        // now, the same as if they had scrolled there themselves.
        userTookOverRef.current = true;
    }, [resultsReplaced, scrollRef, virtualizer]);

    // Held in a ref so the effect below can call the current one without
    // listing it as a dependency. Its identity changes whenever the highlight
    // moves, and depending on that is what made a click scroll: picking a card
    // with the mouse is not a request to move it.
    const placeHighlightRef = useRef(placeHighlight);
    placeHighlightRef.current = placeHighlight;

    useLayoutEffect(() => {
        // A request is the keyboard driving again, so it takes the scroll back.
        userTookOverRef.current = false;
        placeHighlightRef.current();
        // No second pass of our own here: the virtualizer runs one every frame
        // until the offset it resolves stops moving, and unlike a scheduled
        // callback it is not cancelled by the next keypress.
        //
        // Only a request scrolls. highlightScrollRequest is a counter, so the
        // same highlight asked for twice scrolls twice; the keyboard, the
        // folder tree and the chat all bump it, and a click deliberately does
        // not. layoutSignature is here because a settings change throws away
        // every measured height, and the card the user was reading would
        // otherwise end up somewhere else on screen.
    }, [highlightScrollRequest, layoutSignature]);

    // Where the highlighted row sits in the list, and how tall it is. Both
    // move long after the scroll has been written, which is why placing it
    // once is not enough: walking the list quickly lands on cards whose
    // preview has not arrived, so the card placed is a skeleton and the card
    // that ends up there is several times taller — most of all this one, which
    // shows every element because it is highlighted. Rows above it arriving
    // move it too, without changing its size, so its offset counts as well.
    const highlighted =
        highlightedIndex === -1
            ? undefined
            : virtualizer.measurementsCache[highlightedIndex];
    const highlightedStart = highlighted?.start ?? null;
    const highlightedSize = highlighted?.size ?? null;
    useLayoutEffect(() => {
        if (userTookOverRef.current) return;
        placeHighlightRef.current();
        // Deliberately not depending on the callback: this corrects a
        // placement that has already been asked for, as the row it was aimed
        // at settles. A highlight the user moved by hand has not asked for
        // anything, and `mousedown` has already recorded that they are driving.
    }, [highlightedStart, highlightedSize]);

    if (resultOrder.length === 0 && !temporaryFileId) {
        if (!isLoading) return <EmptySearchResults />;
        // Carries the list's own style: the skeleton reads the spacing from
        // the same variables the cards it stands in for will.
        return (
            <div className={styles.cardContainer} style={listStyle}>
                <ResultCardSkeleton />
            </div>
        );
    }

    return (
        <div
            className={styles.cardContainer}
            ref={containerRef}
            data-row-chrome="flat"
            {...{ [COLUMN_HOST_ATTR]: "" }}
            style={listStyle}
        >
            {showColumns && <FieldColumnHeader />}
            <div
                className={styles.virtualList}
                data-testid="virtual-list"
                ref={listRef}
                style={{ height: virtualizer.getTotalSize() }}
            >
                {/* The window of rendered rows, moved as one. Offsetting the
                window rather than every row is what lets the rows inside it
                lay out against each other. */}
                <div
                    className={styles.virtualWindow}
                    style={{
                        transform: `translateY(${
                            (virtualizer.getVirtualItems()[0]?.start ?? 0) -
                            virtualizer.options.scrollMargin
                        }px)`,
                    }}
                >
                    {virtualizer.getVirtualItems().map((item) => {
                        const fileId = orderedFileIds[item.index];
                        if (fileId === undefined) return null;
                        return (
                            <ResultRow
                                key={item.key}
                                index={item.index}
                                measureElement={virtualizer.measureElement}
                                recordHeight={recordHeight}
                                // The card draws a skeleton until its preview
                                // is in hand and its real self afterwards,
                                // which is a different height.
                                hasPreview={files[fileId]?.preview != null}
                                isHighlighted={
                                    fileId === highlightedFileId &&
                                    !highlightPendingRow
                                }
                            >
                                <ResultCard
                                    fileId={fileId}
                                    isHighlighted={
                                        fileId === highlightedFileId &&
                                        !highlightPendingRow
                                    }
                                    stale={files[fileId]?.stale ?? false}
                                    isTemporary={fileId === temporaryFileId}
                                    isTourAnchor={fileId === tourAnchorFileId}
                                />
                            </ResultRow>
                        );
                    })}
                </div>
            </div>
            {isPaginating && (
                <div
                    className={styles.pendingPageRow}
                    data-highlighted={highlightPendingRow ? "true" : undefined}
                    data-testid="pending-page-row"
                >
                    <ResultCardSkeleton />
                </div>
            )}
            <LoadMoreButton />
        </div>
    );
});

DetailedView.displayName = "DetailedView";
