import { MoreVert, Preview } from "@mui/icons-material";
import { IconButton, Menu, MenuItem, useMediaQuery } from "@mui/material";
import { t } from "i18next";
import { UpdateHiddenButton } from "../../common/components/files/UpdateHiddenButton";
import styles from "./FileActions.module.css";
import { DownloadButton } from "../../common/components/DownloadButton";
import { ReIndexButton } from "../components/ReIndexButton";
import { SummaryButton } from "../components/SummaryButton";
import { useState, ReactNode, useCallback } from "react";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { GetFilePreviewResponse } from "../../../app/api";
import { TagsList } from "../../common/components/tags/TagsList";
import { TagsInput } from "../../common/components/tags/TagsInput";
import { ShareButton } from "../components/ShareButton";
import {
    selectQuery,
    setFileDetailData,
    setIsDetailsOpen,
} from "../searchSlice";
import { UpdateFlaggedButton } from "../../common/components/files/UpdateFlaggedButton";
import { UpdateSeenButton } from "../../common/components/files/UpdateSeenButton";
import { TranslationButton } from "../components/TranslationButton";

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

    const handleViewDetail = useCallback(() => {
        dispatch(
            setFileDetailData({
                filePreview: filePreview,
                searchQuery: searchQuery,
            }),
        );
        dispatch(setIsDetailsOpen(true));
    }, [dispatch, filePreview, searchQuery]);

    const actions: ReactNode[] = [
        <UpdateFlaggedButton
            key="flag"
            icon_only={true}
            filePreview={filePreview}
            fileFlagged={filePreview.flagged}
        />,
        <UpdateSeenButton
            key="seen"
            icon_only={true}
            filePreview={filePreview}
            fileSeen={filePreview.seen}
        />,
        <TagsInput
            key="tags-input"
            icon_only={true}
            filePreview={filePreview}
        />,
        <ShareButton key="share" fileId={filePreview.fileId} />,
        <IconButton
            key="preview"
            aria-label="preview"
            title={t("generalSearchView.viewDetails")}
            onClick={() => {
                if (isMobile) handleMenuClose();
                handleViewDetail();
            }}
        >
            <Preview />
        </IconButton>,
        <TranslationButton key="translate" filePreview={filePreview} />,
        <SummaryButton key="summarize" filePreview={filePreview} />,
        <ReIndexButton key="re-index" file_id={filePreview.fileId} />,
        <DownloadButton key="download" fileId={filePreview.fileId} />,
        <UpdateHiddenButton
            key="visibility"
            icon_only={true}
            filePreview={filePreview}
            fileHidden={filePreview.hidden}
        />,
    ];

    const actionButtons = [...actions, ...(additionalActions ?? [])];

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
            <TagsList tags={filePreview.tags || []} filePreview={filePreview} />
            <div className={styles.fileActionButtons}>{actionButtons}</div>
        </div>
    );
}
