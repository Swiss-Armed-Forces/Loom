import { MoreVert, Preview } from "@mui/icons-material";
import { IconButton, Menu, MenuItem } from "@mui/material";
import { t } from "i18next";
import { UpdateVisibilityButton } from "../../common/components/files/UpdateVisibilityStateButton";
import { IconButtonDownloadMenu } from "../../common/components/IconButtonDownloadMenu";
import { ReIndexButton } from "../components/ReIndexButton";
import { SummaryButton } from "../components/SummaryButton";
import { TranslationDialog } from "../components/TranslationDialog";
import { useState } from "react";
import { useAppDispatch } from "../../../app/hooks";
import { FileDialogDetailData } from "../model";
import { showFileDetailDialog } from "../../common/commonSlice";
import { GetFilePreviewResponse } from "../../../app/api";
import { TagsList } from "../../common/components/tags/TagsList";
import { TagsInput } from "../../common/components/tags/TagsInput";
import { ShareButton } from "../components/ShareButton";
import styles from "./ResultCardAction.module.css";

interface ResultCardActions {
    isMobile: boolean;
    fileId: string;
    filePreview: GetFilePreviewResponse;
}

export function ResultCardActions({
    isMobile,
    fileId,
    filePreview,
}: ResultCardActions) {
    const dispatch = useAppDispatch();
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);

    const handleMenuClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleViewDetail = (fileDetailData: FileDialogDetailData) => {
        dispatch(showFileDetailDialog(fileDetailData));
    };

    if (isMobile) {
        return (
            <>
                <IconButton onClick={handleMenuClick}>
                    <MoreVert />
                </IconButton>
                <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                    <MenuItem>
                        <TagsInput
                            icon_only={true}
                            tagsAlreadyAssignedToFile={filePreview.tags}
                            file_id={filePreview.fileId}
                        />
                    </MenuItem>
                    <MenuItem>
                        <ShareButton fileId={fileId} />
                    </MenuItem>
                    <MenuItem>
                        <IconButton
                            title={t("generalSearchView.viewContent")}
                            onClick={() => {
                                handleMenuClose();
                                handleViewDetail({
                                    fileId,
                                });
                            }}
                        >
                            <Preview />
                        </IconButton>
                    </MenuItem>
                    <MenuItem>
                        <TranslationDialog file_id={fileId} />
                    </MenuItem>
                    <MenuItem>
                        <SummaryButton file_id={fileId} />
                    </MenuItem>
                    <MenuItem>
                        <ReIndexButton file_id={fileId} />
                    </MenuItem>
                    <MenuItem>
                        <IconButtonDownloadMenu fileId={fileId} />
                    </MenuItem>
                    <MenuItem onClick={handleMenuClose}>
                        <UpdateVisibilityButton
                            file_id={fileId}
                            icon_only={true}
                            fileHidden={filePreview.hidden}
                        />
                    </MenuItem>
                </Menu>
            </>
        );
    }
    return (
        <div className={styles.resultCardActions}>
            <TagsList
                tags={filePreview.tags || []}
                fileId={filePreview.fileId}
            />
            <TagsInput
                icon_only={true}
                tagsAlreadyAssignedToFile={filePreview.tags}
                file_id={filePreview.fileId}
            />
            <div className={styles.MuiCardHeaderActionButtons}>
                <ShareButton fileId={fileId} />
                <IconButton
                    title={t("generalSearchView.viewContent")}
                    onClick={() =>
                        handleViewDetail({
                            fileId,
                        })
                    }
                >
                    <Preview />
                </IconButton>
                <TranslationDialog file_id={fileId} />
                <SummaryButton file_id={fileId} />
                <ReIndexButton file_id={fileId} />
                <IconButtonDownloadMenu fileId={fileId} />
                <UpdateVisibilityButton
                    icon_only={true}
                    file_id={fileId}
                    fileHidden={filePreview.hidden}
                />
            </div>
        </div>
    );
}
