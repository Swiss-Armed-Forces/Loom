import {
    Badge,
    Box,
    Card,
    CardActions,
    CardContent,
    Skeleton,
    Typography,
} from "@mui/material";
import { useMediaQuery } from "@mui/material";
import React, { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useInView } from "react-intersection-observer";
import { toast } from "react-toastify";

import {
    GetFilePreviewResponse,
    scheduleSingleFileIndexing,
    scheduleSingleFileSummarization,
    scheduleSingleFileTranslation,
    scheduleSingleImageDescription,
    updateFile,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import {
    selectQuery,
    selectFileById,
    selectAutoActionsPreferences,
    setFileInViewState,
    setFilePreview,
    setHighlightedIndex,
} from "@app/slices/searchSlice";
import { webApiGetFileThumbnail } from "@features/common/urls";
import { DialogType } from "@features/common/utils/enums";
import { FileDetailTab } from "@features/common/utils/enums";
import {
    FileCardHeader,
    HighlightList,
    TagsList,
} from "@features/search/components";

import { FileTasksList } from "./FileTasksList";
import styles from "./ResultCard.module.css";
import { Summary } from "./Summary";

interface ResultCardProps {
    fileId: string;
    index: number;
    isHighlighted?: boolean;
}

export const ResultCard = React.memo(
    ({ fileId, index, isHighlighted = false }: ResultCardProps) => {
        const dispatch = useAppDispatch();
        const { t } = useTranslation();
        const isMobile = useMediaQuery("(max-width:900px)");
        const searchQuery = useAppSelector(selectQuery);
        const file = useAppSelector(selectFileById(fileId));
        const filePreview = file?.preview;
        const sortFieldValue = file?.meta?.sortFieldValue ?? "";
        const cardRef = useRef<HTMLDivElement>(null);
        const { ref: inViewRef, inView } = useInView({
            threshold: [0.2],
        });
        const autoActionsPreferences = useAppSelector(
            selectAutoActionsPreferences,
        );
        const hasUpdatedSeen = useRef<boolean>(true);
        const hasHighlightActionsRun = useRef<boolean>(false);

        // Custom scroll function that scrolls within the results container only
        const scrollCardIntoView = () => {
            if (!cardRef.current) return;

            // Find the scrollable parent container (searchResultWrapper)
            const scrollContainer = cardRef.current.closest(
                "[class*='searchResultWrapper']",
            );

            if (!scrollContainer) {
                // Fallback to basic scrollIntoView if container not found
                cardRef.current.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest",
                });
                return;
            }

            const card = cardRef.current;
            const cardRect = card.getBoundingClientRect();
            const containerRect = scrollContainer.getBoundingClientRect();

            // Calculate the target scroll position to center the card
            // with some offset to show context (not perfectly centered, slightly above)
            const cardCenterOffset = cardRect.top - containerRect.top;
            const containerVisibleHeight = containerRect.height;
            const targetScrollTop =
                scrollContainer.scrollTop +
                cardCenterOffset -
                containerVisibleHeight / 3; // Position card at 1/3 from top

            scrollContainer.scrollTo({
                top: Math.max(0, targetScrollTop),
                behavior: "smooth",
            });
        };

        // Scroll into view when highlighted
        useEffect(() => {
            if (isHighlighted && cardRef.current) {
                scrollCardIntoView();
            }
        }, [isHighlighted]);

        // Reset hasUpdatedSeen when file changes
        // Do not reset it if the file is still highlighted
        useEffect(() => {
            if (
                isHighlighted ||
                !hasUpdatedSeen ||
                filePreview?.seen == undefined ||
                filePreview?.seen
            ) {
                return;
            }
            hasUpdatedSeen.current = false;
            hasHighlightActionsRun.current = false;
        }, [filePreview?.seen, isHighlighted]);

        // Re-scroll when content loads (skeleton replaced with actual content)
        // This handles the case where card height changes after preview loads
        useEffect(() => {
            const runHighlightAutoActions = (file: GetFilePreviewResponse) => {
                const prefs = autoActionsPreferences;
                const optimisticUpdates: Partial<GetFilePreviewResponse> = {};

                if (prefs.markAsSeen && !file.seen) {
                    updateFile(file.fileId, { seen: true }).catch((err) =>
                        toast.error(
                            t("updateFileState.seen.scheduledErrorToast", {
                                err,
                            }),
                        ),
                    );
                    hasUpdatedSeen.current = true;
                    optimisticUpdates.seen = true;
                }

                if (prefs.flag && !file.flagged) {
                    updateFile(file.fileId, { flagged: true }).catch((err) =>
                        toast.error(
                            t("updateFileState.flagged.scheduledErrorToast", {
                                err,
                            }),
                        ),
                    );
                    optimisticUpdates.flagged = true;
                }

                if (prefs.reindex) {
                    scheduleSingleFileIndexing(file.fileId).catch(() => {});
                }

                if (prefs.summarize) {
                    scheduleSingleFileSummarization(file.fileId, null).catch(
                        () => {},
                    );
                }

                if (prefs.describeImage) {
                    scheduleSingleImageDescription(file.fileId, null).catch(
                        () => {},
                    );
                }

                if (prefs.translate) {
                    scheduleSingleFileTranslation("", file.fileId).catch(
                        () => {},
                    );
                }

                if (Object.keys(optimisticUpdates).length > 0) {
                    dispatch(setFilePreview({ ...file, ...optimisticUpdates }));
                }
            };

            if (isHighlighted && filePreview && cardRef.current) {
                if (!hasHighlightActionsRun.current) {
                    hasHighlightActionsRun.current = true;
                    runHighlightAutoActions(filePreview);
                }
                // Small delay to allow DOM to update after content renders
                const timeoutId = setTimeout(() => {
                    scrollCardIntoView();
                }, 100);
                cardRef.current.focus();
                return () => {
                    clearTimeout(timeoutId);
                };
            }
        }, [isHighlighted, filePreview]); // eslint-disable-line react-hooks/exhaustive-deps

        // Combine refs
        const setRefs = (element: HTMLDivElement | null) => {
            cardRef.current = element;
            inViewRef(element);
        };

        useEffect(() => {
            dispatch(
                setFileInViewState({
                    fileId: fileId,
                    inView: inView,
                    query: searchQuery,
                }),
            );
        }, [inView, fileId, searchQuery?.id]); // eslint-disable-line react-hooks/exhaustive-deps

        const handleCardClick = (
            e:
                | React.MouseEvent<HTMLDivElement>
                | React.FocusEvent<HTMLDivElement>,
        ) => {
            const target = e.target as HTMLElement;

            // Ignore clicks from IconButtons
            if (!target.closest(".MuiIconButton-root")) {
                dispatch(setHighlightedIndex(index));
            }
        };

        const handleOpenDetailsOnTabClick = (tab: FileDetailTab) => {
            if (!filePreview) return;
            dispatch(
                openDialog({
                    id: "",
                    type: DialogType.FileDetail,
                    props: {
                        fileId: filePreview.fileId,
                        searchQuery: searchQuery,
                        tab,
                    },
                }),
            );
        };

        return (
            <Box
                className="resultCardParent"
                tabIndex={0}
                data-highlighted={isHighlighted ? "true" : undefined}
                ref={setRefs}
                onClick={handleCardClick}
                onFocus={handleCardClick}
                sx={{
                    cursor: "pointer",
                    position: "relative",
                    ...(isHighlighted && {
                        "&::before": {
                            content: '""',
                            position: "absolute",
                            inset: -2,
                            borderRadius: 1.5,
                            border: 2,
                            borderStyle: "solid",
                            borderColor: "secondary.main",
                            boxShadow: (theme) =>
                                `0 0 8px ${theme.palette.secondary.main}80, 0 0 16px ${theme.palette.secondary.main}4D`,
                            pointerEvents: "none",
                            zIndex: 1,
                        },
                    }),
                }}
            >
                {!filePreview ? (
                    <div className={styles.skeletonLoadingContainer}>
                        <div className={styles.skeletonLoadingAvatar}>
                            <Skeleton
                                variant="circular"
                                width={50}
                                height={50}
                            />
                            <Skeleton variant="text" style={{ flexGrow: 1 }} />
                        </div>
                        <Skeleton variant="text" />
                        <Skeleton variant="text" />
                        <Skeleton variant="text" />
                    </div>
                ) : (
                    <Card>
                        <FileCardHeader filePreview={filePreview} />
                        <CardContent className={styles.cardContent}>
                            <div className={styles.contentColumn}>
                                <Summary
                                    filePreview={filePreview}
                                    onOpenDetailsTab={
                                        handleOpenDetailsOnTabClick
                                    }
                                />
                                <HighlightList
                                    highlights={
                                        filePreview.highlight as Record<
                                            string,
                                            string[]
                                        >
                                    }
                                />
                                {isMobile && (
                                    <TagsList
                                        tags={filePreview.tags || []}
                                        filePreview={filePreview}
                                    />
                                )}
                            </div>

                            {filePreview.thumbnailFileId && (
                                <Badge
                                    color="primary"
                                    badgeContent={
                                        filePreview.thumbnailTotalFrames
                                    }
                                    anchorOrigin={{
                                        vertical: "bottom",
                                        horizontal: "right",
                                    }}
                                    className={styles.thumbnailBadge}
                                >
                                    <img
                                        onClick={() =>
                                            handleOpenDetailsOnTabClick(
                                                FileDetailTab.Rendered,
                                            )
                                        }
                                        className={styles.resultImage}
                                        src={webApiGetFileThumbnail(
                                            filePreview.fileId,
                                            filePreview.thumbnailFileId,
                                        )}
                                        alt="Thumbnail"
                                    />
                                </Badge>
                            )}
                        </CardContent>
                        <CardActions className={styles.cardActions}>
                            <Typography
                                variant="caption"
                                className={styles.sortFieldCaption}
                                sx={{
                                    color: "text.secondary",
                                }}
                            >{`${searchQuery?.sortField ?? "score"}: ${sortFieldValue}`}</Typography>
                            <FileTasksList
                                tasksSucceeded={
                                    filePreview.tasksSucceeded || []
                                }
                                tasksFailed={filePreview.tasksFailed || []}
                                taskRetried={filePreview.tasksRetried || []}
                            ></FileTasksList>
                        </CardActions>
                    </Card>
                )}
            </Box>
        );
    },
);

ResultCard.displayName = "ResultCard";
