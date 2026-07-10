import { MoreVert } from "@mui/icons-material";
import {
    IconButton,
    Menu,
    MenuItem,
    Typography,
    useMediaQuery,
} from "@mui/material";
import { useState, useEffect, ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse, RenderedFile } from "@app/api";
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

import { menuJKNavigation } from "../menuKeyboardNav";

import styles from "./FileActions.module.css";

interface FileActionsProps {
    filePreview: GetFilePreviewResponse;
    additionalActions?: ReactNode[];
    hideDetail?: boolean;
    renderedFile?: RenderedFile;
}

export const FileActions = ({
    filePreview,
    additionalActions = [],
    hideDetail,
    renderedFile,
}: FileActionsProps) => {
    const { t } = useTranslation();
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

    useEffect(() => {
        const close = () => setAnchorEl(null);
        document.addEventListener("loom:close-menus", close);
        return () => document.removeEventListener("loom:close-menus", close);
    }, []);

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
        <DownloadButton
            key="download"
            fileId={filePreview.fileId}
            renderedFile={renderedFile}
        />,
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

    const overflowActions: { button: ReactNode; label: string }[] = [
        {
            button: (
                <TranslationButton
                    key="translate"
                    filePreview={filePreview}
                    iconOnly
                />
            ),
            label: t("sideMenu.translateQueriedFiles"),
        },
        {
            button: (
                <SummaryButton
                    key="summarize"
                    filePreview={filePreview}
                    iconOnly
                />
            ),
            label: t("summarizationDialog.executeButton"),
        },
        {
            button: (
                <ImageDescriptionButton
                    key="describe-image"
                    filePreview={filePreview}
                    iconOnly
                />
            ),
            label: t("imageDescriptionButton.describeImage"),
        },
        {
            button: (
                <ReIndexButton key="re-index" fileId={filePreview.fileId} />
            ),
            label: t("sideMenu.reIndexQueriedFiles"),
        },
        {
            button: (
                <UpdateHiddenButton
                    key="visibility"
                    iconOnly
                    filePreview={filePreview}
                    fileHidden={filePreview.hidden}
                />
            ),
            label: filePreview.hidden
                ? t("updateFileState.hidden.disable")
                : t("updateFileState.hidden.enable"),
        },
    ];

    if (isMobile) {
        const allActions = [
            ...primaryActions,
            ...overflowActions.map(({ button }) => button),
        ];
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
                <Menu
                    anchorEl={anchorEl}
                    open={open}
                    onClose={handleMenuClose}
                    onKeyDown={menuJKNavigation}
                >
                    {overflowActions.map(({ button, label }) => (
                        <MenuItem
                            key={(button as React.ReactElement).key}
                            sx={{ p: 0.5, gap: 1 }}
                            onClick={(e) => {
                                // Delegate clicks on the label to the button.
                                if (
                                    !(e.target as HTMLElement).closest("button")
                                ) {
                                    e.currentTarget
                                        .querySelector<HTMLButtonElement>(
                                            "button",
                                        )
                                        ?.click();
                                }
                                handleMenuClose();
                            }}
                        >
                            {button}
                            <Typography variant="body2" sx={{ flexShrink: 0 }}>
                                {label}
                            </Typography>
                        </MenuItem>
                    ))}
                </Menu>
                {/* Hidden buttons keep hotkey-mapped actions (r, S, T) in the
                    container DOM so clickActionButton() can find them even when
                    the overflow menu is closed. */}
                <div style={{ display: "none" }}>
                    <ReIndexButton fileId={filePreview.fileId} />
                    <SummaryButton filePreview={filePreview} iconOnly />
                    <TranslationButton filePreview={filePreview} iconOnly />
                </div>
            </div>
        </div>
    );
};
