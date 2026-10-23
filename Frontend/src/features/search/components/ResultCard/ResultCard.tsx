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
import { FOLLOW_TAB } from "@app/slices/fileDetailSelection";
import {
    RightSidebarTab,
    selectQuery,
    selectFileById,
    selectCardElementVisibility,
    selectFieldLayout,
    selectPreviewFields,
    ensureViewPreview,
    fileInViewChanged,
    setDetailTab,
    setHighlightedFileId,
    setRightSidebarTab,
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

/* Hoisted out of the component: `sx` is re-serialised for every object it is
given, and a result list mounts and unmounts dozens of cards a second while it
is being scrolled. These never vary, so they are built once. */
const CARD_PARENT_SX = { cursor: "pointer", outline: "none" } as const;
const CARD_PARENT_STALE_SX = {
    cursor: "pointer",
    outline: "none",
    opacity: 0.7,
} as const;
const CARD_CONTENT_SX = {
    py: "var(--loom-card-padding, 0.5rem)",
    px: { xs: 1, sm: 2 },
    wordBreak: "break-word",
    "&:last-child": { pb: "var(--loom-card-padding, 0.5rem)" },
} as const;
const STACKED_CONTENT_ROW_SX = {
    display: "flex",
    gap: 2,
    flexDirection: { xs: "column", md: "row" },
} as const;
const FIELDS_COLUMN_SX = { flex: 1, minWidth: 0 } as const;
/* The card as two columns: everything that is text, and the picture. */
const CARD_BODY_ROW_SX = { display: "flex", alignItems: "stretch" } as const;
const CARD_MAIN_COLUMN_SX = { flex: 1, minWidth: 0 } as const;
/**
 * Keeps the frame count inside the thumbnail it counts.
 *
 * MUI anchors a badge on the corner and then translates it half its own size
 * past it, so a quarter of the bubble hangs below the image. The card is a
 * `Paper`, which clips to its rounded corners, and the room under the image is
 * the card's bottom padding - which the spacing presets shrink. The bottom of
 * the count lost 5px of itself to it.
 *
 * Sitting the bubble flush inside the corner makes it independent of the
 * padding, so no spacing can cut it.
 */
const THUMBNAIL_BADGE_SX = {
    "& .MuiBadge-badge": { transform: "none" },
} as const;
/* Fills the side column. Through `sx` rather than the stylesheet because
MUI's own `.MuiBadge-root` sets `position: relative`, and a class from the CSS
module loses to it; `sx` is emotion's and wins. Without this the image keeps
its intrinsic height and sits at the top of a column it should fill. */
const SIDE_THUMBNAIL_BADGE_SX = {
    ...THUMBNAIL_BADGE_SX,
    position: "absolute",
    top: 0,
    left: 0,
    // Explicit rather than `inset: 0`: the badge is a flex box that sizes to
    // its image, and anchoring all four edges left it at the image's own
    // height instead of the column's. A percentage resolves against the
    // column, which the text beside it has already given a height.
    width: "100%",
    height: "100%",
} as const;
const FOOTER_ROW_SX = {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    mt: 1,
} as const;
const TEMPORARY_CHIP_SX = { fontSize: "0.7rem" } as const;
const SORT_CAPTION_SX = { color: "text.disabled", pl: 0.5 } as const;

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
        const vis = useAppSelector(selectCardElementVisibility);
        const fieldLayout = useAppSelector(selectFieldLayout);
        // Every card draws the same elements, the highlighted one included.
        // It used to force all of them on, which made it taller than the slot
        // the list had measured for it - so it was drawn over its neighbour
        // until the measurement caught up, and the list moved under the reader
        // as the highlight travelled. The highlight is a mark on a card now,
        // not a different card.
        const hasThumbnailSlot = reservesThumbnailSlot(fieldLayout, vis);
        const thumbnailFileId =
            vis.thumbnailWidthRem > 0 ? filePreview?.thumbnailFileId : null;
        // The field block follows the field selection and nothing else. It
        // used to have a switch of its own as well, which could only ever
        // disagree with the selection: a reader who wants no fields on the
        // card has one way to say so, which is to select none under Card
        // Fields.
        const hasSelectedFields = useAppSelector(
            (state) => selectPreviewFields(state).length > 0,
        );
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
                    handleOpenInTab(FileDetailTab.Rendered, true);
                } else {
                    dispatch(setHighlightedFileId(fileId));
                }
            }
        };

        const handleOpenInTab = (tab: FileDetailTab, background = false) => {
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

        // "Why did this fail?" - answered on the following tab rather than
        // in a tab of its own. The highlight already puts the file in the
        // sidebar, so this only has to say which part of it to show.
        const handleShowTasks = () => {
            dispatch(setHighlightedFileId(fileId));
            dispatch(
                setDetailTab({
                    target: FOLLOW_TAB,
                    detailTab: FileDetailTab.Tasks,
                }),
            );
            dispatch(setRightSidebarTab(RightSidebarTab.FILE_DETAIL));
        };

        /*
         * Stop the browser selecting a word on the second click.
         *
         * Double-clicking a card opens it, and the native behaviour on top of
         * that is a highlighted word - usually a chunk of the file path - left
         * behind on every open. `detail > 1` is the second click of the pair,
         * so an ordinary drag still selects text and the first click still
         * takes focus.
         *
         * Not gated on `isInteractiveTarget`: the path and the chips are what
         * the selection usually lands in, and cancelling a mousedown's default
         * does not cancel the click that follows it, so their own actions are
         * untouched.
         */
        const handleCardMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
            if (e.detail > 1) e.preventDefault();
        };

        const handleCardDoubleClick = (e: React.MouseEvent<HTMLDivElement>) => {
            if (!isInteractiveTarget(e.target)) {
                handleOpenInTab(FileDetailTab.Rendered, false);
            }
        };

        // Nothing but padding when there is no field selected, no image and
        // no footer, so the block is left out rather than drawn empty.
        const hasCardBody =
            hasSelectedFields ||
            Boolean(thumbnailFileId) ||
            isTemporary ||
            vis.showSortIndicator;

        // Beside the whole card rather than inside its content block. The
        // reserved slot of the line layout keeps its own place in the row, so
        // that the card's columns stay under the header above the list.
        //
        // Reserved from the setting and not from the file, and so empty on a
        // file that has no image: a column that came and went with the file
        // left the fields of one card sitting to the left of the fields of
        // the next.
        const reservesSideThumbnail =
            vis.thumbnailWidthRem > 0 && !hasThumbnailSlot;

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
                    sx={
                        reservesSideThumbnail
                            ? SIDE_THUMBNAIL_BADGE_SX
                            : THUMBNAIL_BADGE_SX
                    }
                    className={
                        hasThumbnailSlot ? undefined : styles.thumbnailBadge
                    }
                >
                    {/* No click of its own: the picture is part of the card,
                    so it highlights on a single click and opens a tab on a
                    double one like the rest of the row. */}
                    <img
                        className={
                            hasThumbnailSlot
                                ? styles.lineThumbnailImage
                                : styles.fullHeightImage
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
                data-tour-anchor={isTourAnchor ? "true" : undefined}
                ref={setRefs}
                onMouseDown={handleCardMouseDown}
                onClick={handleCardClick}
                onDoubleClick={handleCardDoubleClick}
                onFocus={handleCardClick}
                sx={stale ? CARD_PARENT_STALE_SX : CARD_PARENT_SX}
            >
                {!filePreview ? (
                    <ResultCardSkeleton />
                ) : (
                    <ResultCardSurface
                        isHighlighted={isHighlighted}
                        seen={filePreview.seen}
                        flat
                    >
                        <Box
                            sx={
                                reservesSideThumbnail
                                    ? CARD_BODY_ROW_SX
                                    : undefined
                            }
                        >
                            <Box
                                sx={
                                    reservesSideThumbnail
                                        ? CARD_MAIN_COLUMN_SX
                                        : undefined
                                }
                            >
                                <FileCardHeader
                                    filePreview={filePreview}
                                    onStateChipClick={handleShowTasks}
                                    // No `compact`: the header measures its own
                                    // width and lays itself out from that,
                                    // which is what unrolls the file actions
                                    // into clickable icons where there is room
                                    // for them. Pinning it on took that away
                                    // however wide the card was.
                                    denseChrome
                                    showExtensionIcon={vis.showExtensionIcon}
                                    showFilePath={vis.showFilePath}
                                    showParentNavigation={
                                        vis.showParentNavigation
                                    }
                                    showStatusIndicators={
                                        vis.showStatusIndicators
                                    }
                                    showAttachments={vis.showAttachments}
                                    showTags={vis.showTags}
                                    showActions={vis.showActions}
                                    // Also for the card the tour points at:
                                    // its step is about the actions, and at
                                    // the default spacing they are drawn for
                                    // no card the reader is not on.
                                    keyboardActionsOnly={
                                        isHighlighted || isTourAnchor
                                    }
                                    bodyFollows={hasCardBody}
                                    singleLineRow={fieldLayout === "line"}
                                />
                                {hasCardBody && (
                                    <CardContent sx={CARD_CONTENT_SX}>
                                        <Box
                                            className={
                                                hasThumbnailSlot
                                                    ? styles.lineContentRow
                                                    : undefined
                                            }
                                            sx={
                                                hasThumbnailSlot
                                                    ? undefined
                                                    : STACKED_CONTENT_ROW_SX
                                            }
                                            data-tour="result-card-content"
                                        >
                                            {hasSelectedFields && (
                                                <Box sx={FIELDS_COLUMN_SX}>
                                                    <FieldSections
                                                        filePreview={
                                                            filePreview
                                                        }
                                                    />
                                                </Box>
                                            )}
                                            {hasThumbnailSlot && (
                                                // Empty on a file without a thumbnail:
                                                // the slot is what keeps this card's
                                                // columns under the header's.
                                                <Box
                                                    className={
                                                        styles.lineThumbnailSlot
                                                    }
                                                >
                                                    {thumbnail}
                                                </Box>
                                            )}
                                        </Box>
                                        {(isTemporary ||
                                            vis.showSortIndicator) && (
                                            <Box sx={FOOTER_ROW_SX}>
                                                {isTemporary ? (
                                                    <Chip
                                                        icon={<SearchOff />}
                                                        label={t(
                                                            "detailedView.outsideLoadedResults",
                                                        )}
                                                        size="small"
                                                        color="warning"
                                                        variant="outlined"
                                                        sx={TEMPORARY_CHIP_SX}
                                                    />
                                                ) : (
                                                    <Typography
                                                        variant="caption"
                                                        sx={SORT_CAPTION_SX}
                                                    >{`${searchQuery?.sortField ?? "score"}: ${sortFieldValue}`}</Typography>
                                                )}
                                            </Box>
                                        )}
                                    </CardContent>
                                )}
                            </Box>
                            {reservesSideThumbnail && (
                                <Box className={styles.thumbnailColumn}>
                                    {thumbnail}
                                </Box>
                            )}
                        </Box>
                    </ResultCardSurface>
                )}
            </Box>
        );
    },
);

ResultCard.displayName = "ResultCard";
