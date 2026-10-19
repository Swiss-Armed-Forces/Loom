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
    hideDetail?: boolean;
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
}

/** Stable identity for the common "no tags" case, so TagsList sees the same
 *  array on every render instead of a fresh one. */
const NO_TAGS: string[] = [];

/** Avatar edge length on a dense card. */
const COMPACT_AVATAR_SIZE_PX = 24;

const TITLE_SX = { flex: 1 } as const;
const DENSE_TITLE_SX = {
    flex: 1,
    p: 0.75,
    // The action cluster reserves a row of 40px buttons that a dense card
    // cannot spare, so it is claimed only while the card is under the pointer
    // or holds focus.
    "& .MuiCardHeader-action": {
        opacity: 0,
        transition: "opacity 0.15s",
    },
    [`&:hover .MuiCardHeader-action,
      &:focus-within .MuiCardHeader-action`]: { opacity: 1 },
    // Nothing ever hovers on a touch screen, so show them there.
    "@media (hover: none)": {
        "& .MuiCardHeader-action": { opacity: 1 },
    },
} as const;
const ROW_SX = {
    display: "flex",
    alignItems: "center",
    gap: 1,
    minWidth: 0,
} as const;
const COMPACT_ROW_SX = { ...ROW_SX, gap: 0.5 } as const;
const COLUMN_SX = {
    display: "flex",
    flexDirection: "column",
    gap: 0.5,
} as const;
const CENTERED_ROW_SX = { display: "flex", alignItems: "center" } as const;

export const FileCardHeader = memo(
    ({
        filePreview,
        additionalActions,
        hideDetail,
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
        // Never inferred from the width: a narrow pane is not a dense list.
        const isDense = denseChrome;

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
                sx={isDense ? DENSE_TITLE_SX : TITLE_SX}
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
                    <Box sx={COLUMN_SX}>
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
                }
                action={
                    showActions ? (
                        <FileActions
                            filePreview={filePreview}
                            additionalActions={additionalActions}
                            hideDetail={hideDetail}
                            renderedFile={renderedFile}
                            isCompact={isCompact}
                        />
                    ) : undefined
                }
            />
        );
    },
);

FileCardHeader.displayName = "FileCardHeader";
