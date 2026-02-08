import { CardHeader, Box } from "@mui/material";
import { ContentCut } from "@mui/icons-material";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { GetFilePreviewResponse } from "../../../app/api";
import styles from "./FileCardHeader.module.css";
import { selectQuery, updateQuery } from "../searchSlice";
import { ClickableFilePath } from "../components/ClickableFilePath";
import { updateFileExtensionOfQuery } from "../SearchQueryUtils";
import { FileAvatar } from "../components/FileAvatar";
import { ReactNode } from "react";
import { FileActions } from "./FileActions";
import { FileAttachments } from "./FileAttachments";

interface FileCardHeaderProps {
    filePreview: GetFilePreviewResponse;
    additionalActions?: ReactNode[];
}

export function FileCardHeader({
    filePreview,
    additionalActions,
}: FileCardHeaderProps) {
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);

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
        <CardHeader
            className={styles.resultCardHeader}
            sx={{ flex: 1, padding: 0 }}
            avatar={
                <FileAvatar
                    fileExtension={filePreview.fileExtension}
                    performSearch={() =>
                        handleQueryReplaceFileExtension(
                            filePreview.fileExtension,
                        )
                    }
                />
            }
            title={
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <span>{filePreview.name}</span>
                    <FileAttachments
                        attachments={filePreview.attachments}
                    ></FileAttachments>
                    {filePreview.contentIsTruncated && (
                        <ContentCut
                            fontSize="small"
                            titleAccess="Content is truncated"
                        />
                    )}
                </Box>
            }
            subheader={<ClickableFilePath fullPath={filePreview.path} />}
            action={
                <FileActions
                    filePreview={filePreview}
                    additionalActions={additionalActions}
                />
            }
        />
    );
}
