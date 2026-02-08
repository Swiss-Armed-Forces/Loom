import { MoreVert, Preview } from "@mui/icons-material";
import { IconButton, Menu, MenuItem, useMediaQuery } from "@mui/material";
import { t } from "i18next";
import { UpdateVisibilityButton } from "../../common/components/files/UpdateVisibilityStateButton";
import { IconButtonDownloadMenu } from "../../common/components/IconButtonDownloadMenu";
import { ReIndexButton } from "../components/ReIndexButton";
import { SummaryButton } from "../components/SummaryButton";
import { TranslationDialog } from "../components/TranslationDialog";
import { useState, ReactNode } from "react";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { GetFilePreviewResponse } from "../../../app/api";
import { TagsList } from "../../common/components/tags/TagsList";
import { TagsInput } from "../../common/components/tags/TagsInput";
import { ShareButton } from "../components/ShareButton";
import styles from "./FileActions.module.css";
import { selectQuery, setFileDetailData } from "../searchSlice";
import { OpenButton } from "../components/OpenButton";

interface FileActionsProps {
    filePreview: GetFilePreviewResponse;
    additionalActions?: ReactNode[];
}

export function FileActions({
    filePreview,
    additionalActions,
}: FileActionsProps) {
    const dispatch = useAppDispatch();
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const searchQuery = useAppSelector(selectQuery);
    const open = Boolean(anchorEl);
    const isMobile = useMediaQuery("(max-width:1200px)");

    const handleMenuClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleViewDetail = () => {
        dispatch(
            setFileDetailData({
                filePreview: filePreview,
                searchQuery: searchQuery,
            }),
        );
    };

    const actionButtons = [
        <TagsInput
            key="tags-input"
            icon_only={true}
            tagsAlreadyAssignedToFile={filePreview.tags}
            file_id={filePreview.fileId}
        />,
        <ShareButton key="share" fileId={filePreview.fileId} />,
        <IconButton
            key="preview"
            title={t("generalSearchView.viewDetails")}
            onClick={() => {
                if (isMobile) handleMenuClose();
                handleViewDetail();
            }}
        >
            <Preview />
        </IconButton>,
        <TranslationDialog key="translation" file_id={filePreview.fileId} />,
        <SummaryButton key="summary" file_id={filePreview.fileId} />,
        <ReIndexButton key="reindex" file_id={filePreview.fileId} />,
        <OpenButton key="open" file_id={filePreview.fileId} />,
        <IconButtonDownloadMenu key="download" fileId={filePreview.fileId} />,
        <UpdateVisibilityButton
            key="visibility"
            icon_only={true}
            file_id={filePreview.fileId}
            fileHidden={filePreview.hidden}
        />,
        ...(additionalActions ?? []),
    ];

    if (isMobile) {
        return (
            <>
                <IconButton onClick={handleMenuClick}>
                    <MoreVert />
                </IconButton>
                <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                    {actionButtons.map((button, index) => (
                        <MenuItem
                            key={index}
                            onClick={
                                index === actionButtons.length - 1
                                    ? handleMenuClose
                                    : undefined
                            }
                        >
                            {button}
                        </MenuItem>
                    ))}
                </Menu>
            </>
        );
    }

    return (
        <div className={styles.fileActions}>
            <TagsList
                tags={filePreview.tags || []}
                fileId={filePreview.fileId}
            />
            <div className={styles.fileActionButtons}>{actionButtons}</div>
        </div>
    );
}
