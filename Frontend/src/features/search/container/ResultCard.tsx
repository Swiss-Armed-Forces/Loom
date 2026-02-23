import React, { useEffect, useRef } from "react";
import {
    Badge,
    Box,
    Card,
    CardActions,
    CardContent,
    CardMedia,
    Skeleton,
    styled,
    Typography,
    TypographyProps,
} from "@mui/material";

import {
    selectQuery,
    selectFileById,
    setFileInViewState,
    setFileDetailData,
    setHighlightedIndex,
} from "../searchSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";

import styles from "./ResultCard.module.css";

import { FileDetailTab } from "../model";
import { useTranslation } from "react-i18next";
import { Tasks } from "../../common/components/tasks/Tasks";
import { EllipsisButton } from "../components/EllipsisButton";
import { webApiGetFileThumbnail } from "../../common/urls";
import { useInView } from "react-intersection-observer";
import { HighlightList } from "./HighlightList";
import { useMediaQuery } from "@mui/material";
import { TagsList } from "../../common/components/tags/TagsList";
import { FileCardHeader } from "./FileCardHeader";

const FieldTypography = styled(Typography)<TypographyProps>`
    line-height: 1.2;
`;

interface ResultCardProps {
    fileId: string;
    index: number;
    isHighlighted?: boolean;
}

export const ResultCard: React.FC<ResultCardProps> = React.memo(
    ({ fileId, index, isHighlighted = false }: ResultCardProps) => {
        const dispatch = useAppDispatch();
        const { t } = useTranslation();
        const isMobile = useMediaQuery("(max-width:900px)");
        const searchQuery = useAppSelector(selectQuery);
        const file = useAppSelector(selectFileById(fileId));
        const filePreview = file?.preview;
        const sortFieldValue = file?.meta.sortFieldValue ?? "";
        const cardRef = useRef<HTMLDivElement>(null);
        const { ref: inViewRef, inView } = useInView({
            threshold: [0.2],
        });

        // Custom scroll function that scrolls within the results container only
        const scrollCardIntoView = () => {
            if (!cardRef.current) return;

            // Find the scrollable parent container (searchResultWrapper)
            const scrollContainer = cardRef.current.closest(
                "[class*='searchResultWrapper']",
            ) as HTMLElement | null;

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

        // Re-scroll when content loads (skeleton replaced with actual content)
        // This handles the case where card height changes after preview loads
        useEffect(() => {
            if (isHighlighted && filePreview && cardRef.current) {
                // Small delay to allow DOM to update after content renders
                const timeoutId = setTimeout(() => {
                    scrollCardIntoView();
                }, 100);
                return () => clearTimeout(timeoutId);
            }
        }, [isHighlighted, filePreview]);

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
                }),
            );
        }, [
            inView,
            fileId,
            searchQuery, // this is required here as we want to re-run this every time the user changes query. The same file might be in the old and new query results
            dispatch,
        ]);

        const handleCardClick = () => {
            // Select this card when clicked
            dispatch(setHighlightedIndex(index));
        };

        return (
            <Box
                className="resultCardParent"
                data-highlighted={isHighlighted ? "true" : undefined}
                ref={setRefs}
                onClick={handleCardClick}
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
                                {filePreview.summary == null ||
                                filePreview.summary == "" ? null : (
                                    <fieldset
                                        className={styles.summaryHighlightText}
                                    >
                                        <div className={styles.summaryText}>
                                            {filePreview.summary}
                                        </div>

                                        <legend
                                            className={
                                                styles.summaryHighlightTitle
                                            }
                                        >
                                            <div className={styles.summaryText}>
                                                {t("generalSearchView.summary")}
                                            </div>
                                        </legend>
                                    </fieldset>
                                )}

                                <FieldTypography
                                    className={`${styles.resultHighlightText} ${styles.contentText}`}
                                >
                                    {filePreview.content}
                                    {filePreview.contentPreviewIsTruncated && (
                                        <EllipsisButton
                                            click={() => {
                                                dispatch(
                                                    setFileDetailData({
                                                        filePreview:
                                                            filePreview,
                                                        searchQuery:
                                                            searchQuery,
                                                        tab: FileDetailTab.Content,
                                                    }),
                                                );
                                            }}
                                            title={t(
                                                "generalSearchView.viewDetails",
                                            )}
                                        />
                                    )}
                                </FieldTypography>
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
                                        fileId={filePreview.fileId}
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
                                    <div className={styles.thumbnailWrapper}>
                                        <CardMedia
                                            component="img"
                                            onClick={() => {
                                                dispatch(
                                                    setFileDetailData({
                                                        filePreview:
                                                            filePreview,
                                                        searchQuery:
                                                            searchQuery,
                                                        tab: FileDetailTab.Rendered,
                                                    }),
                                                );
                                            }}
                                            className={styles.resultImage}
                                            image={webApiGetFileThumbnail(
                                                filePreview.fileId,
                                                filePreview.thumbnailFileId,
                                            )}
                                            alt="Thumbnail"
                                        />
                                    </div>
                                </Badge>
                            )}
                        </CardContent>
                        <CardActions className={styles.cardActions}>
                            <Typography
                                variant="caption"
                                color="text.secondary"
                                className={styles.sortFieldCaption}
                            >{`${searchQuery?.sortField ?? "score"}: ${sortFieldValue}`}</Typography>
                            <Tasks
                                tasksSucceeded={
                                    filePreview.tasksSucceeded || []
                                }
                                tasksFailed={filePreview.tasksFailed || []}
                                taskRetried={filePreview.tasksRetried || []}
                            ></Tasks>
                        </CardActions>
                    </Card>
                )}
            </Box>
        );
    },
);

ResultCard.displayName = "ResultCard";
