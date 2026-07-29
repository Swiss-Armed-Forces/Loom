import { Skeleton } from "@mui/material";
import React, { useLayoutEffect, useMemo, useRef } from "react";

import { useAppSelector } from "@app/hooks";
import { selectIsLoading } from "@app/slices/commonSlice";
import {
    selectFiles,
    selectHighlightedFileId,
    selectHighlightScrollMode,
    selectHighlightScrollRequest,
    selectTemporaryFileId,
} from "@app/slices/searchSlice";
import {
    EmptySearchResults,
    LoadMoreButton,
    ResultCard,
} from "@features/search/components";

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

export const DetailedView: React.FC = React.memo(() => {
    const files = useAppSelector(selectFiles);
    const isLoading = useAppSelector(selectIsLoading);
    const highlightedFileId = useAppSelector(selectHighlightedFileId);
    const highlightScrollRequest = useAppSelector(selectHighlightScrollRequest);
    const highlightScrollMode = useAppSelector(selectHighlightScrollMode);
    const temporaryFileId = useAppSelector(selectTemporaryFileId);
    const containerRef = useRef<HTMLDivElement>(null);

    useLayoutEffect(() => {
        if (!containerRef.current) return;
        scrollHighlightedCardIntoView(
            containerRef.current,
            highlightScrollMode,
        );
    }, [highlightScrollRequest, highlightScrollMode]);

    const allFileIds = useMemo(
        () =>
            Object.keys(files).filter((fileId) => files[fileId].meta !== null),
        [files],
    );

    if (allFileIds.length === 0 && !temporaryFileId) {
        if (!isLoading) return <EmptySearchResults />;
        return (
            <div className={styles.skeletonLoadingContainer}>
                <div className={styles.skeletonLoadingAvatar}>
                    <Skeleton variant="circular" width={50} height={50} />
                    <Skeleton variant="text" style={{ flexGrow: 1 }} />
                </div>
                <Skeleton variant="text" />
                <Skeleton variant="text" />
                <Skeleton variant="text" />
            </div>
        );
    }

    return (
        <div className={styles.cardContainer} ref={containerRef}>
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
