import { MoreVert } from "@mui/icons-material";
import { IconButton, Menu, MenuItem, Tooltip } from "@mui/material";
import { useState, useEffect, ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse, RenderedFile } from "@app/api";
import { useAppSelector } from "@app/hooks";
import { selectQuery } from "@app/slices/searchSlice";
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

interface ActionDef {
    key: string;
    tooltip: string;
    render: (disableTooltip: boolean) => ReactNode;
}

interface FileActionsProps {
    filePreview: GetFilePreviewResponse;
    additionalActions?: ReactNode[];
    hideDetail?: boolean;
    renderedFile?: RenderedFile;
    isCompact: boolean;
}

export const FileActions = ({
    filePreview,
    additionalActions = [],
    hideDetail,
    renderedFile,
    isCompact,
}: FileActionsProps) => {
    const { t } = useTranslation();
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const searchQuery = useAppSelector(selectQuery);
    const open = Boolean(anchorEl);

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

    const primaryActionDefs: ActionDef[] = [
        {
            key: "flag",
            tooltip: filePreview.flagged
                ? t("updateFileState.flagged.disable")
                : t("updateFileState.flagged.enable"),
            render: (disableTooltip) => (
                <UpdateFlaggedButton
                    key="flag"
                    iconOnly
                    filePreview={filePreview}
                    fileFlagged={filePreview.flagged}
                    disableTooltip={disableTooltip}
                />
            ),
        },
        {
            key: "seen",
            tooltip: filePreview.seen
                ? t("updateFileState.seen.disable")
                : t("updateFileState.seen.enable"),
            render: (disableTooltip) => (
                <UpdateSeenButton
                    key="seen"
                    iconOnly
                    filePreview={filePreview}
                    fileSeen={filePreview.seen}
                    disableTooltip={disableTooltip}
                />
            ),
        },
        {
            key: "tags-input",
            tooltip: t("tags.addTag"),
            render: (disableTooltip) => (
                <AddTagsButton
                    key="tags-input"
                    iconOnly
                    filePreview={filePreview}
                    disableTooltip={disableTooltip}
                />
            ),
        },
        {
            key: "share",
            tooltip: t("generalSearchView.shareContent.title"),
            render: (disableTooltip) => (
                <ShareButton
                    key="share"
                    fileId={filePreview.fileId}
                    disableTooltip={disableTooltip}
                />
            ),
        },
        {
            key: "download",
            tooltip: t("downloadWarning.title"),
            render: (disableTooltip) => (
                <DownloadButton
                    key="download"
                    fileId={filePreview.fileId}
                    renderedFile={renderedFile}
                    disableTooltip={disableTooltip}
                />
            ),
        },
    ];

    if (!hideDetail) {
        primaryActionDefs.push({
            key: "preview",
            tooltip: t("generalSearchView.viewDetails"),
            render: (disableTooltip) => (
                <ViewDetailButton
                    key="preview"
                    fileId={filePreview.fileId}
                    searchQuery={searchQuery}
                    disableTooltip={disableTooltip}
                />
            ),
        });
    }

    const primaryActions: ReactNode[] = primaryActionDefs.map((d) =>
        d.render(false),
    );
    // additionalActions are caller-supplied (e.g. the close button in FileDetailPanel)
    // and must always be visible — keep them in primaryActions.
    primaryActions.push(...additionalActions);

    const overflowActions: ActionDef[] = [
        {
            key: "translate",
            tooltip: t("sideMenu.translateQueriedFiles"),
            render: () => (
                <TranslationButton
                    key="translate"
                    filePreview={filePreview}
                    iconOnly
                    disableTooltip
                />
            ),
        },
        {
            key: "summarize",
            tooltip: t("summarizationDialog.executeButton"),
            render: () => (
                <SummaryButton
                    key="summarize"
                    filePreview={filePreview}
                    iconOnly
                    disableTooltip
                />
            ),
        },
        {
            key: "describe-image",
            tooltip: t("imageDescriptionButton.describeImage"),
            render: () => (
                <ImageDescriptionButton
                    key="describe-image"
                    filePreview={filePreview}
                    iconOnly
                    disableTooltip
                />
            ),
        },
        {
            key: "re-index",
            tooltip: t("sideMenu.reIndexQueriedFiles"),
            render: () => (
                <ReIndexButton
                    key="re-index"
                    fileId={filePreview.fileId}
                    disableTooltip
                />
            ),
        },
        {
            key: "visibility",
            tooltip: filePreview.hidden
                ? t("updateFileState.hidden.disable")
                : t("updateFileState.hidden.enable"),
            render: () => (
                <UpdateHiddenButton
                    key="visibility"
                    iconOnly
                    filePreview={filePreview}
                    fileHidden={filePreview.hidden}
                    disableTooltip
                />
            ),
        },
    ];

    const renderMenuItems = (actions: ActionDef[]) =>
        actions.map(({ key, tooltip, render }) => (
            <Tooltip key={key} title={tooltip} placement="left">
                <MenuItem
                    onClick={(e) => {
                        if (!(e.target as HTMLElement).closest("button")) {
                            e.currentTarget
                                .querySelector<HTMLButtonElement>("button")
                                ?.click();
                        }
                        handleMenuClose();
                    }}
                >
                    {render(true)}
                </MenuItem>
            </Tooltip>
        ));

    if (isCompact) {
        return (
            <div data-tour="result-card-actions">
                <IconButton onClick={handleMenuClick}>
                    <MoreVert />
                </IconButton>
                <Menu
                    anchorEl={anchorEl}
                    open={open}
                    onClose={handleMenuClose}
                    onKeyDown={menuJKNavigation}
                >
                    {renderMenuItems(primaryActionDefs)}
                    {additionalActions.map((action, i) => (
                        <MenuItem
                            key={
                                (action as React.ReactElement).key ??
                                `additional-${i}`
                            }
                            onClick={(e) => {
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
                            {action}
                        </MenuItem>
                    ))}
                    {renderMenuItems(overflowActions)}
                </Menu>
                {/* Hidden buttons keep hotkey-mapped actions in the DOM so
                clickActionButton() can find them even when the menu is closed. */}
                <div style={{ display: "none" }}>
                    {!hideDetail && (
                        <ViewDetailButton
                            fileId={filePreview.fileId}
                            searchQuery={searchQuery}
                        />
                    )}
                    <UpdateFlaggedButton
                        iconOnly
                        filePreview={filePreview}
                        fileFlagged={filePreview.flagged}
                    />
                    <UpdateSeenButton
                        iconOnly
                        filePreview={filePreview}
                        fileSeen={filePreview.seen}
                    />
                    <AddTagsButton iconOnly filePreview={filePreview} />
                    <ShareButton fileId={filePreview.fileId} />
                    <DownloadButton
                        fileId={filePreview.fileId}
                        renderedFile={renderedFile}
                    />
                    <TranslationButton filePreview={filePreview} iconOnly />
                    <SummaryButton filePreview={filePreview} iconOnly />
                    <ReIndexButton fileId={filePreview.fileId} />
                </div>
            </div>
        );
    }

    return (
        <div
            className={styles.fileActionButtons}
            data-tour="result-card-actions"
        >
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
                {renderMenuItems(overflowActions)}
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
    );
};
