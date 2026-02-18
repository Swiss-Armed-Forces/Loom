import React, { useEffect } from "react";
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
} from "../searchSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";

import styles from "./ResultCard.module.css";

import { FileDetailTab } from "../model";
import { useTranslation } from "react-i18next";
import { Tasks } from "../../common/components/tasks/Tasks.tsx";
import { EllipsisButton } from "../components/EllipsisButton.tsx";
import { webApiGetFileThumbnail } from "../../common/urls.ts";
import { useInView } from "react-intersection-observer";
import { HighlightList } from "./HighlightList.tsx";
import { useMediaQuery } from "@mui/material";
import { TagsList } from "../../common/components/tags/TagsList.tsx";
import { FileCardHeader } from "./FileCardHeader.tsx";

const FieldTypography = styled(Typography)<TypographyProps>`
    line-height: 1.2;
`;

interface ResultCardProps {
    fileId: string;
}

export const ResultCard: React.FC<ResultCardProps> = React.memo(
    ({ fileId }: ResultCardProps) => {
        const dispatch = useAppDispatch();
        const { t } = useTranslation();
        const isMobile = useMediaQuery("(max-width:900px)");
        const searchQuery = useAppSelector(selectQuery);
        const file = useAppSelector(selectFileById(fileId));
        const filePreview = file?.preview;
        const sortFieldValue = file?.meta.sortFieldValue ?? "";
        const { ref, inView } = useInView({
            threshold: [0.2],
        });

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

        return (
            <div className="resultCardParent" ref={ref}>
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
                ) : filePreview ? (
                    <Card>
                        <Box>
                            <FileCardHeader filePreview={filePreview} />
                            <CardContent className={styles.resultCardContent}>
                                <Box className={styles.highlights}>
                                    {filePreview.summary == null ||
                                    filePreview.summary == "" ? null : (
                                        <fieldset
                                            className={
                                                styles.summaryHighlightText
                                            }
                                        >
                                            <div className={styles.summaryText}>
                                                {filePreview.summary}
                                            </div>

                                            <legend
                                                className={
                                                    styles.summaryHighlightTitle
                                                }
                                            >
                                                <div
                                                    className={
                                                        styles.summaryText
                                                    }
                                                >
                                                    {"Summary"}
                                                </div>
                                            </legend>
                                        </fieldset>
                                    )}

                                    <FieldTypography
                                        className={styles.resultHighlightText}
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
                                        sx={{ alignSelf: "flex-start" }}
                                    >
                                        <Box sx={{ display: "inline-flex" }}>
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
                                                sx={{
                                                    "object-fit": "contain",
                                                }}
                                                image={webApiGetFileThumbnail(
                                                    filePreview.fileId,
                                                    filePreview.thumbnailFileId,
                                                )}
                                                alt="Thumbnail"
                                            />
                                        </Box>
                                    </Badge>
                                )}
                            </CardContent>
                            <CardActions
                                className={styles.resultCardActionsBottom}
                            >
                                <div className={styles.sortHint}>{`${
                                    searchQuery?.sortField ?? "score"
                                }: ${sortFieldValue}`}</div>
                                <Tasks
                                    tasksSucceeded={
                                        (filePreview.tasksSucceeded &&
                                            filePreview.tasksSucceeded) ||
                                        []
                                    }
                                    tasksFailed={
                                        (filePreview.tasksFailed &&
                                            filePreview.tasksFailed) ||
                                        []
                                    }
                                    taskRetried={
                                        (filePreview.tasksRetried &&
                                            filePreview.tasksRetried) ||
                                        []
                                    }
                                ></Tasks>
                            </CardActions>
                        </Box>
                    </Card>
                ) : null}
            </div>
        );
    },
);

ResultCard.displayName = "ResultCard";
