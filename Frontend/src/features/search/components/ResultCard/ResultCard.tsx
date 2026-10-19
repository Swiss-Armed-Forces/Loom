import { SearchOff } from "@mui/icons-material";
import { Badge, Box, CardContent, Chip, Typography } from "@mui/material";
import React, { useEffect, useLayoutEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useInView } from "react-intersection-observer";

import {
    subscribeChannel,
    unsubscribeChannel,
} from "@app/channelSubscriptions";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectQuery,
    selectFileById,
    selectCardElementVisibility,
    selectFieldLayout,
    selectFlatRowChrome,
    selectResolvedCardDensity,
    ensureViewPreview,
    fileInViewChanged,
    setHighlightedFileId,
    openFileTabThunk,
} from "@app/slices/searchSlice";
import { webApiGetFileThumbnail } from "@features/common/urls";
import { FileDetailTab } from "@features/common/utils/enums";
import { formatCompactNumber } from "@features/common/utils/helpers";
import { FileCardHeader } from "@features/search/components";
import { reservesThumbnailSlot } from "@features/search/components/FieldList/fieldColumns";

import { isInteractiveTarget } from "../interactiveTarget";

import { FieldSections } from "./FieldSections";
import styles from "./ResultCard.module.css";
import { ResultCardSkeleton } from "./ResultCardSkeleton";
import { ResultCardSurface } from "./ResultCardSurface";

interface ResultCardProps {
    fileId: string;
    isHighlighted?: boolean;
    stale?: boolean;
    isTemporary?: boolean;
    /**
     * This is the card the guided tour points at.
     *
     * Passed down rather than read from the tour context here: the context
     * value changes on every step, and subscribing to it from the card would
     * re-render every mounted card each time the tour advances.
     */
    isTourAnchor?: boolean;
}

export const ResultCard = React.memo(
    ({
        fileId,
        isHighlighted = false,
        stale = false,
        isTemporary = false,
        isTourAnchor = false,
    }: ResultCardProps) => {
        const dispatch = useAppDispatch();
        const { t } = useTranslation();
        const searchQuery = useAppSelector(selectQuery);
        const file = useAppSelector((state) => selectFileById(state, fileId));
        const filePreview = file?.preview;
        const sortFieldValue = file?.meta?.sortFieldValue ?? "";
        const visFromStore = useAppSelector(selectCardElementVisibility);
        const resolvedDensity = useAppSelector(selectResolvedCardDensity);
        const fieldLayout = useAppSelector(selectFieldLayout);
        const flatRowChrome = useAppSelector(selectFlatRowChrome);
        // Highlighted card always shows every element regardless of toggles.
        const vis = isHighlighted
            ? {
                  showThumbnails: true,
                  showHighlights: true,
                  showFieldSections: true,
                  showExtensionIcon: true,
                  showFilePath: true,
                  showParentNavigation: true,
                  showStatusIndicators: true,
                  showAttachments: true,
                  showTags: true,
                  showActions: true,
                  showSortIndicator: true,
                  showFieldActions: true,
              }
            : visFromStore;
        // Answered from the store's visibility, never from `vis`: the slot is
        // reserved once for the whole list, so the highlighted card's
        // show-everything override has no say in whether it exists.
        const hasThumbnailSlot = reservesThumbnailSlot(
            fieldLayout,
            visFromStore,
        );
        const thumbnailFileId = vis.showThumbnails
            ? filePreview?.thumbnailFileId
            : null;
        // The highlighted card shows its thumbnail even where the list
        // reserved no column for one - below the line rather than beside it,
        // because a card that widened its own image would take the width out
        // of its own columns and fall out of line with every other row.
        const thumbnailBelowLine = !hasThumbnailSlot && fieldLayout === "line";
        const cardRef = useRef<HTMLDivElement>(null);
        const { ref: inViewRef, inView } = useInView({
            threshold: [0.2],
        });

        useLayoutEffect(() => {
            if (!isHighlighted || !cardRef.current) return;
            cardRef.current.focus({ preventScroll: true });
        }, [isHighlighted]);

        // Combine refs
        const setRefs = (element: HTMLDivElement | null) => {
            cardRef.current = element;
            inViewRef(element);
        };

        // This effect owns the WS channel subscription: it subscribes while the
        // card is in view and the cleanup releases it, so the two stay paired
        // across re-runs and unmount. ensureViewPreview only fills the preview
        // cache, and it may legitimately be skipped. It takes no `query`
        // argument and does not depend on `searchQuery`: the thunk reads the
        // active query from the store itself. Depending on the query object
        // here re-ran this effect for every mounted card whenever its identity
        // changed.
        //
        // fileInViewChanged is dispatched in the body and again in the cleanup
        // because a card can be unmounted while still in view — the list is
        // windowed, so scrolling takes cards away mid-flight. Without the
        // cleanup the id would stay in `filesInView` for the rest of the query.
        useEffect(() => {
            dispatch(fileInViewChanged({ fileId: fileId, inView: inView }));
            if (!inView) return;
            subscribeChannel(fileId, dispatch);
            dispatch(ensureViewPreview({ fileId: fileId }));
            return () => {
                dispatch(fileInViewChanged({ fileId: fileId, inView: false }));
                // unsubscribeChannel is a no-op when not subscribed, but only
                // call it when we subscribed, or the ref count double-decrements
                // and the tab subscription is cancelled prematurely.
                unsubscribeChannel(fileId, dispatch);
            };
        }, [inView, fileId, dispatch]);

        const handleCardClick = (
            e:
                | React.MouseEvent<HTMLDivElement>
                | React.FocusEvent<HTMLDivElement>,
        ) => {
            // Only the card body acts for the card. Anything interactive
            // inside it - an action button, a breadcrumb link, an attachment
            // chip, a popover entry - already performed its own action, and
            // must not open a tab for this file on top of it.
            if (!isInteractiveTarget(e.target)) {
                if (
                    e.type === "click" &&
                    (e as React.MouseEvent<HTMLDivElement>).ctrlKey
                ) {
                    handleOpenDetailsOnTabClick(FileDetailTab.Rendered, true);
                } else {
                    dispatch(setHighlightedFileId(fileId));
                }
            }
        };

        const handleOpenDetailsOnTabClick = (
            tab: FileDetailTab,
            background = false,
        ) => {
            if (!filePreview) return;
            dispatch(setHighlightedFileId(fileId));
            dispatch(
                openFileTabThunk({
                    fileId: filePreview.fileId,
                    detailTab: tab,
                    background,
                }),
            );
        };

        const handleCardDoubleClick = (e: React.MouseEvent<HTMLDivElement>) => {
            if (!isInteractiveTarget(e.target)) {
                handleOpenDetailsOnTabClick(FileDetailTab.Rendered, false);
            }
        };

        // This card shows a thumbnail only because it is highlighted, so the
        // image is being requested right now rather than already in hand.
        const thumbnailOnHighlightOnly =
            isHighlighted && !visFromStore.showThumbnails;

        const thumbnail =
            filePreview && thumbnailFileId ? (
                <Badge
                    data-tour="result-card-preview"
                    color="primary"
                    badgeContent={
                        filePreview.thumbnailTotalFrames != null
                            ? formatCompactNumber(
                                  filePreview.thumbnailTotalFrames,
                              )
                            : undefined
                    }
                    anchorOrigin={{
                        vertical: "bottom",
                        horizontal: "right",
                    }}
                    className={
                        hasThumbnailSlot ? undefined : styles.thumbnailBadge
                    }
                >
                    <img
                        onClick={(e) =>
                            handleOpenDetailsOnTabClick(
                                FileDetailTab.Rendered,
                                e.ctrlKey,
                            )
                        }
                        className={
                            hasThumbnailSlot
                                ? styles.lineThumbnailImage
                                : styles.resultImage
                        }
                        src={webApiGetFileThumbnail(
                            filePreview.fileId,
                            thumbnailFileId,
                        )}
                        alt="Thumbnail"
                    />
                </Badge>
            ) : null;

        const thumbnailBlock =
            thumbnail && thumbnailOnHighlightOnly && !hasThumbnailSlot ? (
                <div className={styles.thumbnailReserve}>{thumbnail}</div>
            ) : (
                thumbnail
            );

        return (
            <Box
                className="resultCardParent"
                tabIndex={0}
                data-highlighted={isHighlighted ? "true" : undefined}
                data-tour="result-card"
                data-tour-anchor={isTourAnchor ? "true" : undefined}
                ref={setRefs}
                onClick={handleCardClick}
                onDoubleClick={handleCardDoubleClick}
                onFocus={handleCardClick}
                sx={{
                    cursor: "pointer",
                    outline: "none",
                    ...(stale && { opacity: 0.7 }),
                }}
            >
                {!filePreview ? (
                    <ResultCardSkeleton />
                ) : (
                    <ResultCardSurface
                        isHighlighted={isHighlighted}
                        seen={filePreview.seen}
                        flat={flatRowChrome}
                    >
                        <FileCardHeader
                            filePreview={filePreview}
                            onStateChipClick={() =>
                                handleOpenDetailsOnTabClick(FileDetailTab.Tasks)
                            }
                            // Spacing owns how tall the header is, the same
                            // as it owns the rest of the card's chrome.
                            compact={resolvedDensity === "compact" || undefined}
                            denseChrome={resolvedDensity === "compact"}
                            showExtensionIcon={vis.showExtensionIcon}
                            showFilePath={vis.showFilePath}
                            showParentNavigation={vis.showParentNavigation}
                            showStatusIndicators={vis.showStatusIndicators}
                            showAttachments={vis.showAttachments}
                            showTags={vis.showTags}
                            showActions={vis.showActions}
                        />
                        {(vis.showFieldSections || thumbnail) && (
                            <CardContent
                                sx={{
                                    py: "var(--loom-card-padding, 0.5rem)",
                                    px: { xs: 1, sm: 2 },
                                    wordBreak: "break-word",
                                    "&:last-child": {
                                        pb: "var(--loom-card-padding, 0.5rem)",
                                    },
                                }}
                            >
                                <Box
                                    className={
                                        hasThumbnailSlot
                                            ? styles.lineContentRow
                                            : undefined
                                    }
                                    sx={
                                        hasThumbnailSlot
                                            ? undefined
                                            : {
                                                  display: "flex",
                                                  gap: 2,
                                                  flexDirection: {
                                                      xs: "column",
                                                      md: "row",
                                                  },
                                              }
                                    }
                                    data-tour="result-card-content"
                                >
                                    {vis.showFieldSections && (
                                        <Box sx={{ flex: 1, minWidth: 0 }}>
                                            <FieldSections
                                                filePreview={filePreview}
                                            />
                                        </Box>
                                    )}
                                    {hasThumbnailSlot ? (
                                        // Empty on a file without a thumbnail:
                                        // the slot is what keeps this card's
                                        // columns under the header's.
                                        <Box
                                            className={styles.lineThumbnailSlot}
                                        >
                                            {thumbnail}
                                        </Box>
                                    ) : (
                                        !thumbnailBelowLine && thumbnailBlock
                                    )}
                                </Box>
                                {thumbnailBelowLine && thumbnail && (
                                    <Box sx={{ mt: 1 }}>{thumbnailBlock}</Box>
                                )}
                                {(isTemporary || vis.showSortIndicator) && (
                                    <Box
                                        sx={{
                                            display: "flex",
                                            justifyContent: "space-between",
                                            alignItems: "center",
                                            mt: 1,
                                        }}
                                    >
                                        {isTemporary ? (
                                            <Chip
                                                icon={<SearchOff />}
                                                label={t(
                                                    "detailedView.outsideLoadedResults",
                                                )}
                                                size="small"
                                                color="warning"
                                                variant="outlined"
                                                sx={{ fontSize: "0.7rem" }}
                                            />
                                        ) : (
                                            <Typography
                                                variant="caption"
                                                sx={{
                                                    color: "text.disabled",
                                                    pl: 0.5,
                                                }}
                                            >{`${searchQuery?.sortField ?? "score"}: ${sortFieldValue}`}</Typography>
                                        )}
                                    </Box>
                                )}
                            </CardContent>
                        )}
                    </ResultCardSurface>
                )}
            </Box>
        );
    },
);

ResultCard.displayName = "ResultCard";
