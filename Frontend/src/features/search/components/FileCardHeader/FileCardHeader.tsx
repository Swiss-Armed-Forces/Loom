import { ContentCut, LinkOff, Translate, Whatshot } from "@mui/icons-material";
import { CardHeader, Box, Chip, IconButton } from "@mui/material";
import { memo, ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse, RenderedFile } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectQuery, updateQuery } from "@app/slices/searchSlice";
import { LazyTooltip } from "@features/common/components";
import { SearchQueryField } from "@features/common/utils/enums";
import { updateFieldOfQuery } from "@features/common/utils/helpers";
import { FileActions } from "@features/search/components";

import { TagsList } from "../TagsList/TagsList";

import { ClickableFilePath } from "./ClickableFilePath";
import { FileAttachments } from "./FileAttachments";
import { FileAvatar } from "./FileAvatar";
import styles from "./FileCardHeader.module.css";
import { NavigateToParent } from "./NavigateToParent";
import { hasVisibleProcessingStatus } from "./processingStatusTour";

const stateChipColor: Record<string, "warning" | "error"> = {
    started: "warning",
    reindexing: "warning",
    failed: "error",
};

interface FileCardHeaderProps {
    filePreview: GetFilePreviewResponse;
    additionalActions?: ReactNode[];
    renderedFile?: RenderedFile;
    onStateChipClick?: () => void;
    /**
     * Lay the header out for a narrow container: tighter gaps, breadcrumbs
     * that ellipsize rather than wrap.
     */
    compact?: boolean;
    /**
     * Dress the header as one row of a dense list: a smaller icon, and the
     * action cluster claimed only on hover.
     *
     * Separate from `compact` because the two are not the same question. The
     * file detail panel is narrow, so it wants the compact layout — but it is
     * a detail view, and hiding its actions behind a hover and shrinking its
     * icon left it looking empty.
     */
    denseChrome?: boolean;
    showExtensionIcon?: boolean;
    showFilePath?: boolean;
    showParentNavigation?: boolean;
    showStatusIndicators?: boolean;
    showAttachments?: boolean;
    showTags?: boolean;
    showActions?: boolean;
    /**
     * Render the actions, but with nothing on screen to show for them.
     *
     * A dozen keyboard shortcuts work by finding the highlighted card in the
     * document and clicking a button inside it, and at the default spacing
     * those buttons are switched off for every card. The highlighted card used
     * to turn them back on, which is why they worked - and why it was taller
     * than its neighbours. Keeping them in the document without drawing them
     * keeps the shortcuts and the equal height both.
     */
    keyboardActionsOnly?: boolean;
    /** Whether the card draws a field block under this header; see
     *  `BODY_FOLLOWS_SX`. */
    bodyFollows?: boolean;
    /** Hold the header to two clipped rows; see `SINGLE_LINE_COLUMN_SX`. */
    singleLineRow?: boolean;
}

/** Stable identity for the common "no tags" case, so TagsList sees the same
 *  array on every render instead of a fresh one. */
const NO_TAGS: string[] = [];

/** Avatar edge length on a dense card. */
const COMPACT_AVATAR_SIZE_PX = 24;

/** Narrower than this and the actions are the overflow menu alone. */
const ACTIONS_UNROLL_PX = 360;

const TITLE_SX = { flex: 1 } as const;
/* The header stops padding where the field block begins, so the gap above the
first field row is the content block's own top padding and matches the gap
below the last one. Left on, the header's 16px sat on top of the content's and
put 24px above the fields against 8px below them. */
const BODY_FOLLOWS_SX = { flex: 1, pb: 0 } as const;
/**
 * The same header, with the action cluster present but not drawn.
 *
 * `display: none` on MUI's own action wrapper rather than on what is inside
 * it: the wrapper carries margins and an alignment of its own, so hiding only
 * its child would still leave the header a different shape from a card that
 * was never given any actions. `click()` reaches a hidden button, which is all
 * the keyboard shortcuts need.
 */
const HIDDEN_ACTIONS_SX = {
    "& .MuiCardHeader-action": { display: "none" },
} as const;
const TITLE_HIDDEN_ACTIONS_SX = { ...TITLE_SX, ...HIDDEN_ACTIONS_SX } as const;
const DENSE_TITLE_SX = {
    flex: 1,
    p: 0.75,
    // The action cluster reserves a row of 40px buttons that a dense card
    // cannot spare, so it is claimed only while the card is under the pointer
    // or holds focus.
    //
    // All of it but the overflow menu, which stays: a card that showed
    // nothing at all until the pointer reached it gave a reader no reason to
    // think there were any actions to go looking for.
    "& .MuiCardHeader-action button": {
        opacity: 0,
        transition: "opacity 0.15s",
    },
    [`& .MuiCardHeader-action button[data-always-visible],
      & .MuiCardHeader-action [data-always-visible] button,
      &:hover .MuiCardHeader-action button,
      &:focus-within .MuiCardHeader-action button`]: { opacity: 1 },
    // Nothing ever hovers on a touch screen, so show them there.
    "@media (hover: none)": {
        "& .MuiCardHeader-action button": { opacity: 1 },
    },
} as const;
const DENSE_TITLE_HIDDEN_ACTIONS_SX = {
    ...DENSE_TITLE_SX,
    ...HIDDEN_ACTIONS_SX,
} as const;
const BODY_FOLLOWS_HIDDEN_ACTIONS_SX = {
    ...BODY_FOLLOWS_SX,
    ...HIDDEN_ACTIONS_SX,
} as const;

const titleSxFor = (
    isDense: boolean,
    actionsHidden: boolean,
    bodyFollows: boolean,
) => {
    if (isDense)
        return actionsHidden ? DENSE_TITLE_HIDDEN_ACTIONS_SX : DENSE_TITLE_SX;
    if (bodyFollows)
        return actionsHidden ? BODY_FOLLOWS_HIDDEN_ACTIONS_SX : BODY_FOLLOWS_SX;
    return actionsHidden ? TITLE_HIDDEN_ACTIONS_SX : TITLE_SX;
};
const ROW_SX = {
    display: "flex",
    alignItems: "center",
    gap: 1,
    minWidth: 0,
} as const;
const COMPACT_ROW_SX = { ...ROW_SX, gap: 0.5 } as const;

/** One row of the header's content column: the path, the tags, the
 *  attachments. */
const META_ROW_HEIGHT = "1.75rem";

const COLUMN_SX = {
    display: "flex",
    flexDirection: "column",
    gap: 0.5,
} as const;
/*
 * The header's content, held to a fixed number of rows and clipped, for the
 * line layout - where every row in the list has to be exactly as tall as
 * every other.
 *
 * On the column rather than on the rows inside it: what grows here is the
 * tag and attachment lists, which wrap to a second line once there are
 * enough of them, and they sit in rows of their own. A height on the column
 * is the one measurement that covers all of them however many there turn out
 * to be. Both lists keep their own overflow control for reaching what does
 * not fit.
 *
 * The count is how many rows the *settings* put here, not how many this file
 * fills, so it is the same for every card - and it is nought when neither is
 * switched on, which is the difference between a tight list and a list of
 * blank space.
 */
const SINGLE_LINE_COLUMN_SX: Record<number, object> = {
    1: { ...COLUMN_SX, height: META_ROW_HEIGHT, overflow: "hidden" },
    2: {
        ...COLUMN_SX,
        height: `calc(2 * ${META_ROW_HEIGHT} + 0.5rem)`,
        overflow: "hidden",
    },
};

const CENTERED_ROW_SX = { display: "flex", alignItems: "center" } as const;

export const FileCardHeader = memo(
    ({
        filePreview,
        additionalActions,
        renderedFile,
        onStateChipClick,
        compact,
        denseChrome = false,
        showExtensionIcon = true,
        showFilePath = true,
        showParentNavigation = true,
        showStatusIndicators = true,
        showAttachments = true,
        showTags = true,
        showActions = true,
        keyboardActionsOnly = false,
        bodyFollows = false,
        singleLineRow = false,
    }: FileCardHeaderProps) => {
        const pathStyle = useMemo(
            () => ({
                color: filePreview.flagged ? "red" : undefined,
                fontWeight: filePreview.seen ? undefined : ("bold" as const),
            }),
            [filePreview.flagged, filePreview.seen],
        );
        const dispatch = useAppDispatch();
        const { t } = useTranslation();
        const searchQuery = useAppSelector(selectQuery);
        const headerRef = useRef<HTMLDivElement>(null);
        const [headerWidth, setHeaderWidth] = useState(0);

        useEffect(() => {
            const el = headerRef.current;
            if (!el) return;
            const ro = new ResizeObserver(([entry]) =>
                setHeaderWidth(entry.contentRect.width),
            );
            ro.observe(el);
            return () => ro.disconnect();
        }, []);

        const isNarrow = headerWidth < 500;
        const isCompact = compact ?? headerWidth < 700;
        /*
         * Whether the actions collapse into the overflow menu alone.
         *
         * Width only, never the `compact` override: a caller asking for the
         * compact *layout* - the detail panel does, because it is a narrow
         * column - is not asking for every action to be put away.
         *
         * The threshold is low because there are only two actions left
         * outside the menu; they fit long before the header is roomy.
         */
        const actionsCollapsed = headerWidth < ACTIONS_UNROLL_PX;
        // Never inferred from the width: a narrow pane is not a dense list.
        const isDense = denseChrome;
        // What the settings put in the header's lower block, which is how
        // tall it has to be held open; see `SINGLE_LINE_COLUMN_SX`.
        const metaRowCount = Number(showAttachments) + Number(showTags);

        const handleFilterByField = (
            field: SearchQueryField,
            value: string,
            negate = false,
            accumulate = false,
        ) => {
            dispatch(
                updateQuery({
                    query: updateFieldOfQuery(
                        searchQuery?.query ?? "",
                        field,
                        value,
                        false,
                        negate,
                        accumulate,
                    ),
                }),
            );
        };

        return (
            <CardHeader
                ref={headerRef}
                className={
                    isCompact
                        ? `${styles.resultCardHeader} ${styles.compactHeader}`
                        : styles.resultCardHeader
                }
                sx={titleSxFor(isDense, !showActions, bodyFollows)}
                avatar={
                    showExtensionIcon ? (
                        <FileAvatar
                            size={isDense ? COMPACT_AVATAR_SIZE_PX : undefined}
                            mimeType={filePreview.mimeType}
                            mimeTypeGroup={filePreview.mimeTypeGroup}
                            performSearch={(negate, accumulate) =>
                                filePreview.mimeType
                                    ? handleFilterByField(
                                          SearchQueryField.FileType,
                                          filePreview.mimeType,
                                          negate,
                                          accumulate,
                                      )
                                    : handleFilterByField(
                                          SearchQueryField.Extension,
                                          filePreview.fileExtension,
                                          negate,
                                          accumulate,
                                      )
                            }
                            hasBadge={!filePreview.seen}
                        />
                    ) : undefined
                }
                title={
                    <Box
                        sx={isCompact ? COMPACT_ROW_SX : ROW_SX}
                        data-tour="result-card-path"
                    >
                        {showParentNavigation && filePreview.parentId && (
                            <NavigateToParent parentId={filePreview.parentId} />
                        )}
                        {showFilePath && (
                            <ClickableFilePath
                                fullPath={filePreview.path}
                                style={pathStyle}
                            />
                        )}
                        {showStatusIndicators &&
                            hasVisibleProcessingStatus(
                                filePreview,
                                isNarrow,
                            ) && (
                                <Box
                                    data-tour="result-card-processing-status"
                                    sx={{
                                        display: "inline-flex",
                                        alignItems: "center",
                                        gap: 1,
                                    }}
                                >
                                    {!isNarrow &&
                                        filePreview.contentIsTruncated && (
                                            <LazyTooltip
                                                title={t(
                                                    "generalSearchView.contentTruncatedIcon",
                                                )}
                                            >
                                                <IconButton
                                                    size="small"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleFilterByField(
                                                            SearchQueryField.ContentTruncated,
                                                            "true",
                                                            e.shiftKey,
                                                            e.ctrlKey,
                                                        );
                                                    }}
                                                >
                                                    <ContentCut fontSize="small" />
                                                </IconButton>
                                            </LazyTooltip>
                                        )}
                                    {!isNarrow &&
                                        filePreview.attachmentsSkipped && (
                                            <LazyTooltip
                                                title={t(
                                                    "generalSearchView.attachmentsSkippedIcon",
                                                )}
                                            >
                                                <IconButton
                                                    size="small"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleFilterByField(
                                                            SearchQueryField.AttachmentsSkipped,
                                                            "true",
                                                            e.shiftKey,
                                                            e.ctrlKey,
                                                        );
                                                    }}
                                                >
                                                    <LinkOff fontSize="small" />
                                                </IconButton>
                                            </LazyTooltip>
                                        )}
                                    {filePreview.state !== "processed" && (
                                        <Chip
                                            size="small"
                                            label={filePreview.state}
                                            color={
                                                stateChipColor[
                                                    filePreview.state
                                                ] ?? "default"
                                            }
                                            variant="outlined"
                                            onClick={
                                                onStateChipClick
                                                    ? (e) => {
                                                          e.stopPropagation();
                                                          onStateChipClick();
                                                      }
                                                    : undefined
                                            }
                                            className={
                                                onStateChipClick
                                                    ? styles.clickableChip
                                                    : undefined
                                            }
                                        />
                                    )}
                                </Box>
                            )}
                        {showStatusIndicators &&
                            !isNarrow &&
                            filePreview.isSpam && (
                                <LazyTooltip
                                    title={t("generalSearchView.spamIcon")}
                                >
                                    <IconButton
                                        size="small"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleFilterByField(
                                                SearchQueryField.IsSpam,
                                                "true",
                                                e.shiftKey,
                                                e.ctrlKey,
                                            );
                                        }}
                                    >
                                        <Whatshot fontSize="small" />
                                    </IconButton>
                                </LazyTooltip>
                            )}
                        {showStatusIndicators &&
                            !isNarrow &&
                            filePreview.detectedLanguage && (
                                <LazyTooltip
                                    title={t(
                                        "generalSearchView.detectedLanguageTooltip",
                                        {
                                            language:
                                                filePreview.detectedLanguage,
                                        },
                                    )}
                                >
                                    <IconButton
                                        size="small"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleFilterByField(
                                                SearchQueryField.DetectedLanguage,
                                                filePreview.detectedLanguage!,
                                                e.shiftKey,
                                                e.ctrlKey,
                                            );
                                        }}
                                    >
                                        <Translate fontSize="small" />
                                    </IconButton>
                                </LazyTooltip>
                            )}
                    </Box>
                }
                subheader={
                    metaRowCount === 0 ? undefined : (
                        <Box
                            sx={
                                singleLineRow
                                    ? SINGLE_LINE_COLUMN_SX[metaRowCount]
                                    : COLUMN_SX
                            }
                        >
                            {showAttachments && (
                                <Box sx={CENTERED_ROW_SX}>
                                    <FileAttachments
                                        attachments={filePreview.attachments}
                                        totalCount={
                                            filePreview.attachmentsTotalCount
                                        }
                                    />
                                </Box>
                            )}
                            {showTags && (
                                <Box data-tour="result-card-tags">
                                    <TagsList
                                        tags={filePreview.tags ?? NO_TAGS}
                                        filePreview={filePreview}
                                    />
                                </Box>
                            )}
                        </Box>
                    )
                }
                action={
                    showActions || keyboardActionsOnly ? (
                        <FileActions
                            filePreview={filePreview}
                            additionalActions={additionalActions}
                            renderedFile={renderedFile}
                            isCompact={actionsCollapsed}
                        />
                    ) : undefined
                }
            />
        );
    },
);

FileCardHeader.displayName = "FileCardHeader";
