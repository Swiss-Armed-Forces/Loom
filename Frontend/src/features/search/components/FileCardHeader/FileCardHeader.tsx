import { ContentCut, Whatshot } from "@mui/icons-material";
import { CardHeader, Box } from "@mui/material";
import { ReactNode } from "react";

import { GetFilePreviewResponse } from "@app/api";
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
}

export const FileCardHeader = ({
    filePreview,
    additionalActions,
    hideDetail,
}: FileCardHeaderProps) => {
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);

    const handleQueryReplaceFileExtension = (extension: string) => {
        dispatch(
            updateQuery({
                query: updateFieldOfQuery(
                    searchQuery?.query ?? "",
                    SearchQueryField.Extension,
                    extension,
                ),
            }),
        );
    };

    return (
        <CardHeader
            className={styles.resultCardHeader}
            sx={{ flex: 1 }}
            avatar={
                <FileAvatar
                    fileExtension={filePreview.fileExtension}
                    performSearch={() => {
                        handleQueryReplaceFileExtension(
                            filePreview.fileExtension,
                        );
                    }}
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
                        <ContentCut
                            fontSize="small"
                            titleAccess="Content is truncated"
                        />
                    )}
                    {filePreview.isSpam && (
                        <Whatshot fontSize="small" titleAccess="SPAM" />
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
                />
            }
        />
    );
};
