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
    const primaryActions: ReactNode[] = [
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
    ];

    if (!hideDetail) {
        primaryActions.push(
            <ViewDetailButton
                key="preview"
                fileId={filePreview.fileId}
                searchQuery={searchQuery}
            />,
        );
    }

    // additionalActions are caller-supplied (e.g. the close button in FileDetailPanel)
    // and must always be visible — keep them in primaryActions.
    primaryActions.push(...additionalActions);

    const overflowActions: ReactNode[] = [
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

    if (isMobile) {
        const allActions = [...primaryActions, ...overflowActions];
        return (
            <>
                <IconButton onClick={handleMenuClick}>
                    <MoreVert />
                </IconButton>
                <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                    {allActions.map((button) => (
                        <MenuItem key={(button as React.ReactElement).key}>
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
            <div className={styles.fileActionButtons}>
                {primaryActions}
                <IconButton
                    size="small"
                    onClick={handleMenuClick}
                    aria-label="more actions"
                >
                    <MoreVert fontSize="small" />
                </IconButton>
                <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                    {overflowActions.map((button) => (
                        <MenuItem
                            key={(button as React.ReactElement).key}
                            sx={{ p: 0.5 }}
                        >
                            {button}
                        </MenuItem>
                    ))}
                </Menu>
            </div>
        </div>
    );
};
