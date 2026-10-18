import React, {
    CSSProperties,
    useEffect,
    useLayoutEffect,
    useMemo,
    useRef,
} from "react";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectIsLoading } from "@app/slices/commonSlice";
import { isLoadedResult } from "@app/slices/searchFileEntry";
import {
    NamedDensity,
    selectCardDensity,
    selectCardElementVisibility,
    selectFieldColumnWidths,
    selectFieldLayout,
    selectFiles,
    selectFlatRowChrome,
    selectHighlightedFileId,
    selectHighlightScrollMode,
    selectHighlightScrollRequest,
    selectPreviewFields,
    selectResolvedCardDensity,
    selectTemporaryFileId,
    selectThumbnailColumnWidth,
    setAutoDetectedDensity,
} from "@app/slices/searchSlice";
import {
    EmptySearchResults,
    LoadMoreButton,
    ResultCard,
} from "@features/search/components";
import { FieldColumnHeader } from "@features/search/components/FieldList/FieldColumnHeader";
import {
    COLUMN_HOST_ATTR,
    FIELD_COLUMNS_VAR,
    columnWidthsOf,
    fieldColumnTemplate,
    reservesThumbnailSlot,
    thumbnailSlotStyle,
} from "@features/search/components/FieldList/fieldColumns";
import { ResultCardSkeleton } from "@features/search/components/ResultCard/ResultCardSkeleton";
import { rowRhythmStyle } from "@features/search/components/ResultCard/rowRhythm";

import styles from "./DetailedView.module.css";

const SCROLL_PADDING_PX = 48;

const scrollHighlightedCardIntoView = (
    container: HTMLDivElement,
    mode: "smart" | "top",
) => {
    const card = container.querySelector(
        '[data-highlighted="true"]',
    ) as HTMLElement | null;
    if (!card) return;

    const scrollContainer = container.closest("[class*='searchPanel']");
    if (!scrollContainer) {
        card.scrollIntoView({ behavior: "instant", block: "nearest" });
        return;
    }

    const cardRect = card.getBoundingClientRect();
    const containerRect = scrollContainer.getBoundingClientRect();
    const cardTop = cardRect.top - containerRect.top;
    const cardBottom = cardTop + card.offsetHeight;
    const visibleHeight = scrollContainer.clientHeight;

    if (mode === "top") {
        // Always align card top to container top + padding (clamped to ≥ 0)
        scrollContainer.scrollTo({
            top: Math.max(
                0,
                scrollContainer.scrollTop + cardTop - SCROLL_PADDING_PX,
            ),
            behavior: "instant",
        });
        return;
    }

    if (
        cardTop >= SCROLL_PADDING_PX &&
        cardBottom <= visibleHeight - SCROLL_PADDING_PX
    )
        return;

    let targetScrollTop: number;
    const cardFitsInView =
        card.offsetHeight <= visibleHeight - 2 * SCROLL_PADDING_PX;
    if (cardTop < SCROLL_PADDING_PX || !cardFitsInView) {
        // Card is above, or too tall to fully show — align card top to container top + padding
        targetScrollTop =
            scrollContainer.scrollTop + cardTop - SCROLL_PADDING_PX;
    } else {
        // Card is below (or too close to bottom) — align card bottom to container bottom - padding
        targetScrollTop =
            scrollContainer.scrollTop +
            cardBottom -
            visibleHeight +
            SCROLL_PADDING_PX;
    }

    scrollContainer.scrollTo({
        top: Math.max(0, targetScrollTop),
        behavior: "instant",
    });
};

const AUTO_DENSITY_BREAKPOINTS: { maxWidth: number; density: NamedDensity }[] =
    [
        { maxWidth: 500, density: "compact" },
        { maxWidth: 850, density: "standard" },
        { maxWidth: Infinity, density: "full" },
    ];

const getDensityForWidth = (width: number): NamedDensity =>
    AUTO_DENSITY_BREAKPOINTS.find((b) => width <= b.maxWidth)!.density;

export const DetailedView: React.FC = React.memo(() => {
    const dispatch = useAppDispatch();
    const files = useAppSelector(selectFiles);
    const isLoading = useAppSelector(selectIsLoading);
    const highlightedFileId = useAppSelector(selectHighlightedFileId);
    const highlightScrollRequest = useAppSelector(selectHighlightScrollRequest);
    const highlightScrollMode = useAppSelector(selectHighlightScrollMode);
    const temporaryFileId = useAppSelector(selectTemporaryFileId);
    const cardDensity = useAppSelector(selectCardDensity);
    const fieldLayout = useAppSelector(selectFieldLayout);
    const previewFields = useAppSelector(selectPreviewFields);
    const columnWidths = useAppSelector(selectFieldColumnWidths);
    const thumbnailWidth = useAppSelector(selectThumbnailColumnWidth);
    const visibility = useAppSelector(selectCardElementVisibility);
    const flatRowChrome = useAppSelector(selectFlatRowChrome);
    const resolvedDensity = useAppSelector(selectResolvedCardDensity);
    const containerRef = useRef<HTMLDivElement>(null);

    // The columns, the row rhythm and the thumbnail slot are published once
    // for the whole list, so the header and every card resolve to the same
    // tracks, the same spacing and the same width kept free on the right.
    const showColumns = fieldLayout === "line" && visibility.showFieldSections;
    const listStyle = {
        [FIELD_COLUMNS_VAR]: fieldColumnTemplate(
            columnWidthsOf(previewFields, columnWidths),
        ),
        ...rowRhythmStyle(resolvedDensity),
        ...thumbnailSlotStyle(
            resolvedDensity,
            reservesThumbnailSlot(fieldLayout, visibility),
            thumbnailWidth,
        ),
    } as CSSProperties;

    // Auto-detect density from container width when not overridden by user.
    useEffect(() => {
        if (cardDensity !== "auto") return;
        const el = containerRef.current;
        if (!el) return;
        let debounce: ReturnType<typeof setTimeout> | null = null;
        const ro = new ResizeObserver(([entry]) => {
            if (debounce) clearTimeout(debounce);
            debounce = setTimeout(() => {
                dispatch(
                    setAutoDetectedDensity(
                        getDensityForWidth(entry.contentRect.width),
                    ),
                );
            }, 100);
        });
        ro.observe(el);
        return () => {
            ro.disconnect();
            if (debounce) clearTimeout(debounce);
        };
    }, [cardDensity, dispatch]);

    useLayoutEffect(() => {
        if (!containerRef.current) return;
        scrollHighlightedCardIntoView(
            containerRef.current,
            highlightScrollMode,
        );
    }, [highlightScrollRequest, highlightScrollMode]);

    const allFileIds = useMemo(
        () =>
            Object.keys(files).filter((fileId) =>
                isLoadedResult(files[fileId]),
            ),
        [files],
    );

    if (allFileIds.length === 0 && !temporaryFileId) {
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
            data-row-chrome={flatRowChrome ? "flat" : undefined}
            {...{ [COLUMN_HOST_ATTR]: "" }}
            style={listStyle}
        >
            {showColumns && <FieldColumnHeader />}
            {temporaryFileId && (
                <ResultCard
                    key={temporaryFileId}
                    fileId={temporaryFileId}
                    isHighlighted={temporaryFileId === highlightedFileId}
                    isTemporary
                />
            )}
            {allFileIds.map((fileId) => (
                <ResultCard
                    key={fileId}
                    fileId={fileId}
                    isHighlighted={fileId === highlightedFileId}
                    stale={files[fileId].stale ?? false}
                />
            ))}
            <LoadMoreButton />
        </div>
    );
});

DetailedView.displayName = "DetailedView";
