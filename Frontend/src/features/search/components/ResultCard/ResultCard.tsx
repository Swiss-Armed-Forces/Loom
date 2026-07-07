import {
    Badge,
    Box,
    Card,
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
import { unsubscribeChannel } from "@app/channelSubscriptions";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectQuery,
    selectFileById,
    selectAutoActionsPreferences,
    setFileInViewState,
    setFilePreview,
    setHighlightedIndex,
    openFileTabThunk,
} from "@app/slices/searchSlice";
import { webApiGetFileThumbnail } from "@features/common/urls";
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
    index?: number;
    isHighlighted?: boolean;
    stale?: boolean;
}

export const ResultCard = React.memo(
    ({
        fileId,
        index = 0,
        isHighlighted = false,
        stale = false,
    }: ResultCardProps) => {
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
                "[class*='searchPanel']",
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

            const cardTop = cardRect.top - containerRect.top;
            const cardBottom = cardTop + cardRect.height;

            // Only scroll if card is outside the visible area
            if (cardTop >= 0 && cardBottom <= containerRect.height) return;

            const containerVisibleHeight = containerRect.height;
            const targetScrollTop =
                scrollContainer.scrollTop +
                cardTop -
                containerVisibleHeight / 3;

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
                cardRef.current.focus({ preventScroll: true });
                return () => {
                    clearTimeout(timeoutId);
                };
            }
        }, [isHighlighted, filePreview, autoActionsPreferences, dispatch, t]);

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
                unsubscribeChannel(fileId, dispatch);
            };
        }, [inView, fileId, searchQuery, dispatch]);

        const handleCardClick = (
            e:
                | React.MouseEvent<HTMLDivElement>
                | React.FocusEvent<HTMLDivElement>,
        ) => {
            const target = e.target as HTMLElement;

            // Ignore clicks from IconButtons
            if (!target.closest(".MuiIconButton-root")) {
                if (
                    e.type === "click" &&
                    (e as React.MouseEvent<HTMLDivElement>).ctrlKey
                ) {
                    handleOpenDetailsOnTabClick(FileDetailTab.Rendered, true);
                } else {
                    dispatch(setHighlightedIndex(index));
                }
            }
        };

        const handleOpenDetailsOnTabClick = (
            tab: FileDetailTab,
            background = false,
        ) => {
            if (!filePreview) return;
            dispatch(setHighlightedIndex(index));
            dispatch(
                openFileTabThunk({
                    fileId: filePreview.fileId,
                    detailTab: tab,
                    background,
                }),
            );
        };

        const handleCardDoubleClick = (e: React.MouseEvent<HTMLDivElement>) => {
            const target = e.target as HTMLElement;
            if (!target.closest(".MuiIconButton-root")) {
                handleOpenDetailsOnTabClick(FileDetailTab.Rendered, e.ctrlKey);
            }
        };

        return (
            <Box
                className="resultCardParent"
                tabIndex={0}
                data-highlighted={isHighlighted ? "true" : undefined}
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
                    <Card
                        sx={{
                            borderLeft: "3px solid",
                            borderColor: isHighlighted
                                ? "primary.main"
                                : "transparent",
                            bgcolor: isHighlighted
                                ? "action.selected"
                                : undefined,
                        }}
                    >
                        <FileCardHeader filePreview={filePreview} />
                        <CardContent
                            sx={{
                                py: 1,
                                px: 2,
                                wordBreak: "break-word",
                                "&:last-child": { pb: 1 },
                            }}
                        >
                            <Box
                                sx={{
                                    display: "flex",
                                    gap: 2,
                                    flexDirection: {
                                        xs: "column",
                                        md: "row",
                                    },
                                }}
                            >
                                <Box
                                    sx={{
                                        flex: 1,
                                        display: "flex",
                                        flexDirection: "column",
                                    }}
                                >
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
                                </Box>

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
                                            onClick={(e) =>
                                                handleOpenDetailsOnTabClick(
                                                    FileDetailTab.Rendered,
                                                    e.ctrlKey,
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
                            </Box>
                            <Box
                                sx={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                    mt: 1,
                                }}
                            >
                                <Typography
                                    variant="caption"
                                    sx={{ color: "text.disabled", pl: 0.5 }}
                                >{`${searchQuery?.sortField ?? "score"}: ${sortFieldValue}`}</Typography>
                                <FileTasksList
                                    tasksSucceeded={
                                        filePreview.tasksSucceeded || []
                                    }
                                    tasksFailed={filePreview.tasksFailed || []}
                                    taskRetried={filePreview.tasksRetried || []}
                                />
                            </Box>
                        </CardContent>
                    </Card>
                )}
            </Box>
        );
    },
);

ResultCard.displayName = "ResultCard";
