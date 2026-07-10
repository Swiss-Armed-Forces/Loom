import { ContentCut, LinkOff, Translate, Whatshot } from "@mui/icons-material";
import { CardHeader, Box, Tooltip } from "@mui/material";
import { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse, RenderedFile } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectQuery, updateQuery } from "@app/slices/searchSlice";
import { SearchQueryField } from "@features/common/utils/enums";
import { updateFieldOfQuery } from "@features/common/utils/helpers";
import { FileActions } from "@features/search/components";

import { ClickableFilePath } from "./ClickableFilePath";
import { FileAttachments } from "./FileAttachments";
import { FileAvatar } from "./FileAvatar";
import styles from "./FileCardHeader.module.css";
import { NavigateToParent } from "./NavigateToParent";

interface FileCardHeaderProps {
    filePreview: GetFilePreviewResponse;
    additionalActions?: ReactNode[];
    hideDetail?: boolean;
    renderedFile?: RenderedFile;
}

export const FileCardHeader = ({
    filePreview,
    additionalActions,
    hideDetail,
    renderedFile,
}: FileCardHeaderProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const searchQuery = useAppSelector(selectQuery);

    const handleFilterByField = (
        field: SearchQueryField,
        value: string,
        negate = false,
    ) => {
        dispatch(
            updateQuery({
                query: updateFieldOfQuery(
                    searchQuery?.query ?? "",
                    field,
                    value,
                    false,
                    negate,
                ),
            }),
        );
    };

    const filterIconSx = {
        cursor: "pointer",
        transition: "transform 0.2s ease",
        "&:hover": { transform: "scale(1.2)" },
        "&:active": { transform: "scale(0.95)" },
    };

    return (
        <CardHeader
            className={styles.resultCardHeader}
            sx={{ flex: 1 }}
            avatar={
                <FileAvatar
                    fileExtension={filePreview.fileExtension}
                    performSearch={(negate) =>
                        handleFilterByField(
                            SearchQueryField.Extension,
                            filePreview.fileExtension,
                            negate,
                        )
                    }
                    hasBadge={!filePreview.seen}
                />
            }
            title={
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    {filePreview.parentId && (
                        <NavigateToParent parentId={filePreview.parentId} />
                    )}
                    <ClickableFilePath
                        fullPath={filePreview.path}
                        style={{
                            color: filePreview.flagged ? "red" : undefined,
                            fontWeight: filePreview.seen ? undefined : "bold",
                        }}
                    />
                    {filePreview.contentIsTruncated && (
                        <Tooltip
                            title={t("generalSearchView.contentTruncatedIcon")}
                        >
                            <ContentCut
                                fontSize="small"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleFilterByField(
                                        SearchQueryField.ContentTruncated,
                                        "true",
                                        e.shiftKey,
                                    );
                                }}
                                sx={filterIconSx}
                            />
                        </Tooltip>
                    )}
                    {filePreview.attachmentsSkipped && (
                        <Tooltip
                            title={t(
                                "generalSearchView.attachmentsSkippedIcon",
                            )}
                        >
                            <LinkOff
                                fontSize="small"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleFilterByField(
                                        SearchQueryField.AttachmentsSkipped,
                                        "true",
                                        e.shiftKey,
                                    );
                                }}
                                sx={filterIconSx}
                            />
                        </Tooltip>
                    )}
                    {filePreview.isSpam && (
                        <Tooltip title={t("generalSearchView.spamIcon")}>
                            <Whatshot
                                fontSize="small"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleFilterByField(
                                        SearchQueryField.IsSpam,
                                        "true",
                                        e.shiftKey,
                                    );
                                }}
                                sx={filterIconSx}
                            />
                        </Tooltip>
                    )}
                    {filePreview.detectedLanguage && (
                        <Tooltip
                            title={t(
                                "generalSearchView.detectedLanguageTooltip",
                                { language: filePreview.detectedLanguage },
                            )}
                        >
                            <Translate
                                fontSize="small"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleFilterByField(
                                        SearchQueryField.DetectedLanguage,
                                        filePreview.detectedLanguage!,
                                        e.shiftKey,
                                    );
                                }}
                                sx={filterIconSx}
                            />
                        </Tooltip>
                    )}
                </Box>
            }
            subheader={
                <Box sx={{ display: "flex", alignItems: "center" }}>
                    <FileAttachments
                        attachments={filePreview.attachments}
                        totalCount={filePreview.attachmentsTotalCount}
                    />
                </Box>
            }
            action={
                <FileActions
                    filePreview={filePreview}
                    additionalActions={additionalActions}
                    hideDetail={hideDetail}
                    renderedFile={renderedFile}
                />
            }
        />
    );
};
