import { SearchOff } from "@mui/icons-material";
import { Badge, Box, CardContent, Chip, Typography } from "@mui/material";
import React, { useEffect, useLayoutEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useInView } from "react-intersection-observer";

import { unsubscribeChannel } from "@app/channelSubscriptions";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectQuery,
    selectFileById,
    selectCardElementVisibility,
    selectFieldLayout,
    selectFlatRowChrome,
    selectResolvedCardDensity,
    setFileInViewState,
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
}

export const ResultCard = React.memo(
    ({
        fileId,
        isHighlighted = false,
        stale = false,
        isTemporary = false,
    }: ResultCardProps) => {
        const dispatch = useAppDispatch();
        const { t } = useTranslation();
        const searchQuery = useAppSelector(selectQuery);
        const file = useAppSelector(selectFileById(fileId));
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

        // Manage the WS channel subscription. setFileInViewState is the single
        // owner of subscribe/unsubscribe when inView changes; the cleanup only
        // handles unmount. unsubscribeChannel is a no-op when not subscribed,
        // so the cleanup is always safe to call.
        useEffect(() => {
            dispatch(
                setFileInViewState({
                    fileId: fileId,
                    inView: inView,
                    query: searchQuery,
                }),
            );
            return () => {
                // Only unsubscribe when inView was true — setFileInViewState does
                // not unsubscribe, so this cleanup is the single owner of that
                // transition. Calling it unconditionally would double-decrement
                // the ref count and cancel the tab subscription prematurely.
                if (inView) unsubscribeChannel(fileId, dispatch);
            };
        }, [inView, fileId, searchQuery, dispatch]);

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

        return (
            <Box
                className="resultCardParent"
                tabIndex={0}
                data-highlighted={isHighlighted ? "true" : undefined}
                data-tour="result-card"
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
                                        !thumbnailBelowLine && thumbnail
                                    )}
                                </Box>
                                {thumbnailBelowLine && thumbnail && (
                                    <Box sx={{ mt: 1 }}>{thumbnail}</Box>
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
