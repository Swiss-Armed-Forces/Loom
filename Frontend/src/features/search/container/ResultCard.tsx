import React, { useEffect, useState } from "react";
import {
    Box,
    Card,
    CardActions,
    CardContent,
    CardHeader,
    CardMedia,
    Skeleton,
    styled,
    Typography,
    TypographyProps,
} from "@mui/material";

import { FileAvatar } from "../components/FileAvatar";
import {
    updateQuery,
    selectQuery,
    selectFileById,
    setFileInViewState,
    setFileDetailData,
} from "../searchSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";

import styles from "./ResultCard.module.css";

import { ClickableFilePath } from "../components/ClickableFilePath";
import { FileDetailTab } from "../model";
import { useTranslation } from "react-i18next";
import { Tasks } from "../../common/components/tasks/Tasks.tsx";
import { EllipsisButton } from "../components/EllipsisButton.tsx";
import { updateFileExtensionOfQuery } from "../SearchQueryUtils.ts";
import { webApiGetFileThumbnail } from "../../common/urls.ts";
import { useInView } from "react-intersection-observer";
import { HighlightList } from "./HighlightList.tsx";
import { ImageDetailDialog } from "../components/ImageDetailDialog.tsx";
import { useMediaQuery } from "@mui/material";
import { ResultCardActions } from "./ResultCardAction.tsx";
import { TagsList } from "../../common/components/tags/TagsList.tsx";

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

        const [imageHashToShow, setImageHashToShow] = useState("");

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

        const handleViewDetail = () => {
            dispatch(
                setFileDetailData({
                    fileId: fileId,
                    tab: FileDetailTab.Content,
                }),
            );
        };

        const handleQueryReplaceFileExtension = (extension: string) => {
            dispatch(
                updateQuery({
                    query: updateFileExtensionOfQuery(
                        searchQuery?.query ?? "",
                        extension,
                    ),
                }),
            );
        };

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
                            <CardHeader
                                className={styles.resultCardHeader}
                                avatar={
                                    <FileAvatar
                                        hasAttachments={
                                            filePreview.hasAttachments
                                        }
                                        isTruncated={
                                            filePreview.contentIsTruncated
                                        }
                                        fileExtension={filePreview.fileExtension
                                            .replace(".", "")
                                            .toLowerCase()}
                                        performSearch={() =>
                                            handleQueryReplaceFileExtension(
                                                filePreview.fileExtension,
                                            )
                                        }
                                    />
                                }
                                title={filePreview.name}
                                subheader={
                                    <ClickableFilePath
                                        fullPath={filePreview.path}
                                    />
                                }
                                action={
                                    <ResultCardActions
                                        isMobile={isMobile}
                                        fileId={fileId}
                                        filePreview={filePreview}
                                    />
                                }
                            ></CardHeader>
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
                                                click={handleViewDetail}
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

                                {filePreview.hasThumbnail && (
                                    <CardMedia
                                        component="img"
                                        onClick={() =>
                                            setImageHashToShow(
                                                filePreview.fileId,
                                            )
                                        }
                                        className={styles.resultImage}
                                        image={webApiGetFileThumbnail(
                                            filePreview.fileId,
                                        )}
                                        alt="Thumbnail of document"
                                    />
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
                <ImageDetailDialog
                    imageHashToShow={imageHashToShow}
                    onClose={() => setImageHashToShow("")}
                />
            </div>
        );
    },
);

ResultCard.displayName = "ResultCard";
