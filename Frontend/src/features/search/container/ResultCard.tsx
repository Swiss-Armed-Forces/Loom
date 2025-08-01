import React, { forwardRef, useEffect, useState } from "react";
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
} from "../searchSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";

import styles from "./ResultCard.module.css";

import { showFileDetailDialog } from "../../common/commonSlice";

import { ClickableFilePath } from "../components/ClickableFilePath";
import { FileDetailViewTab, FileDialogDetailData } from "../model";
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

export const ResultCard = forwardRef<HTMLDivElement, ResultCardProps>(
    ({ fileId }, ref) => {
        const dispatch = useAppDispatch();
        const { t } = useTranslation();
        const isMobile = useMediaQuery("(max-width:900px)");
        const searchQuery = useAppSelector(selectQuery);
        const file = useAppSelector(selectFileById(fileId));
        const filePreview = file?.preview;
        const sortFieldValue = file?.meta.sortFieldValue ?? "";

        const { ref: inViewRef, inView } = useInView({
            threshold: [0, 0.5],
        });

        const [imageHashToShow, setImageHashToShow] = useState("");
        const [initialAnchor, setInitialAnchor] = useState("");

        useEffect(() => {
            function updateInitialAnchor() {
                setInitialAnchor(window.location.hash.substring(1));
            }
            window.addEventListener("hashchange", updateInitialAnchor);
            return () => {
                window.removeEventListener("hashchange", updateInitialAnchor);
            };
        });

        useEffect(() => {
            dispatch(
                setFileInViewState({
                    fileId: fileId,
                    inView: inView,
                }),
            );
        }, [inView, fileId, searchQuery, dispatch]);

        useEffect(() => {
            if (initialAnchor === fileId) {
                handleViewDetail({
                    fileId: fileId,
                });
            }
        }, [fileId, initialAnchor]); // eslint-disable-line react-hooks/exhaustive-deps

        const handleViewDetail = (fileDetailData: FileDialogDetailData) => {
            dispatch(showFileDetailDialog(fileDetailData));
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

        const setRefs = React.useCallback(
            (node: HTMLDivElement | null) => {
                // Ref's from useRef need to have the current value set.
                if (typeof ref === "function") {
                    ref(node);
                } else if (ref) {
                    ref.current = node;
                }
                inViewRef(node);
            },
            [ref, inViewRef],
        );

        return (
            <div className="resultCardParent" ref={setRefs}>
                {!inView && !filePreview ? (
                    <div style={{ height: "200px" }}></div>
                ) : inView && !filePreview ? (
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
                                                click={() =>
                                                    handleViewDetail({
                                                        fileId: fileId,
                                                        tab: FileDetailViewTab.Content,
                                                    })
                                                }
                                                title={t(
                                                    "generalSearchView.viewContent",
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
