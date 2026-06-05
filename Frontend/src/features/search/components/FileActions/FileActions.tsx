import { MoreVert } from "@mui/icons-material";
import { IconButton, Menu, MenuItem, useMediaQuery } from "@mui/material";
import { useState, ReactNode } from "react";

import { GetFilePreviewResponse } from "@app/api";
import { useAppSelector } from "@app/hooks";
import { selectQuery } from "@app/slices/searchSlice";
import { TagsList } from "@features/search/components";
import {
    AddTagsButton,
    DownloadButton,
    ImageDescriptionButton,
    ReIndexButton,
    ShareButton,
    SummaryButton,
    TranslationButton,
    UpdateFlaggedButton,
    UpdateHiddenButton,
    UpdateSeenButton,
    ViewDetailButton,
} from "@features/search/components/FileActionButtons";

import styles from "./FileActions.module.css";

interface FileActionsProps {
    filePreview: GetFilePreviewResponse;
    additionalActions?: ReactNode[];
    hideDetail?: boolean;
}

export const FileActions = ({
    filePreview,
    additionalActions = [],
    hideDetail,
}: FileActionsProps) => {
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
    const actions: ReactNode[] = [
        <UpdateFlaggedButton
            key="flag"
            iconOnly
            filePreview={filePreview}
            fileFlagged={filePreview.flagged}
        />,
        <UpdateSeenButton
            key="seen"
            iconOnly
            filePreview={filePreview}
            fileSeen={filePreview.seen}
        />,
        <AddTagsButton key="tags-input" iconOnly filePreview={filePreview} />,
        <ShareButton key="share" fileId={filePreview.fileId} />,
        <TranslationButton
            key="translate"
            filePreview={filePreview}
            iconOnly
        />,
        <SummaryButton key="summarize" filePreview={filePreview} iconOnly />,
        <ImageDescriptionButton
            key="describe-image"
            filePreview={filePreview}
            iconOnly
        />,
        <ReIndexButton key="re-index" fileId={filePreview.fileId} />,
        <DownloadButton key="download" fileId={filePreview.fileId} />,
        <UpdateHiddenButton
            key="visibility"
            iconOnly
            filePreview={filePreview}
            fileHidden={filePreview.hidden}
        />,
    ];

    if (!hideDetail) {
        actions.splice(
            4,
            0,
            <ViewDetailButton
                key="preview"
                fileId={filePreview.fileId}
                searchQuery={searchQuery}
            />,
        );
    }

    const actionButtons = actions.concat(additionalActions);

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
                filePreview={filePreview}
                maxVisible={3}
            />
            <div className={styles.fileActionButtons}>{actionButtons}</div>
        </div>
    );
};
