import { Delete, Download, Search, Lock } from "@mui/icons-material";
import MenuIcon from "@mui/icons-material/Menu";
import { IconButton, Menu, MenuItem, useMediaQuery } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { ArchiveHit } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { updateQuery } from "@app/slices/searchSlice";
import {
    webApiGetArchive,
    webApiGetArchiveEncrypted,
} from "@features/common/urls";
import { DialogType } from "@features/common/utils/enums";

interface ArchiveActions {
    archive: ArchiveHit;
}

export const ArchiveActions = ({ archive }: ArchiveActions) => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const { t } = useTranslation();
    const matchMedia = useMediaQuery("(max-width: 1300px)");
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

    const handleMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const showArchiveQuery = (archiveId: string) => {
        dispatch(
            updateQuery({
                query: `archives:"${archiveId}"`,
            }),
        );
        navigate("/search");
    };

    const handleDeleteArchive = (archiveId: string) => {
        dispatch(
            openDialog({
                id: "",
                type: DialogType.DeleteArchive,
                props: { archiveId },
            }),
        );
    };

    const hasPlainFile = archive.sha256 != null;
    const hasEncryptedFile = archive.sha256Encrypted != null;

    return (
        <>
            {matchMedia ? (
                <>
                    <IconButton
                        edge="start"
                        color="inherit"
                        aria-label="menu"
                        onClick={handleMenuOpen}
                        data-tour="archive-download-button"
                    >
                        <MenuIcon />
                    </IconButton>
                    <Menu
                        id="simple-menu"
                        anchorEl={anchorEl}
                        keepMounted
                        open={Boolean(anchorEl)}
                        onClose={handleMenuClose}
                    >
                        <MenuItem
                            component="a"
                            href={
                                hasPlainFile
                                    ? webApiGetArchive(archive.fileId)
                                    : undefined
                            }
                            target="_blank"
                            rel="noopener noreferrer"
                            disabled={!hasPlainFile}
                        >
                            <Download />
                            {t("tableView.actions.download")}
                        </MenuItem>
                        <MenuItem
                            component="a"
                            href={
                                hasEncryptedFile
                                    ? webApiGetArchiveEncrypted(archive.fileId)
                                    : undefined
                            }
                            target="_blank"
                            rel="noopener noreferrer"
                            disabled={!hasEncryptedFile}
                        >
                            <Lock />
                            {t("tableView.actions.download_encrypted")}
                        </MenuItem>
                        <MenuItem
                            onClick={() => {
                                showArchiveQuery(archive.fileId);
                            }}
                        >
                            <Search />
                            {t("tableView.actions.search")}
                        </MenuItem>
                        {!archive.hidden && (
                            <MenuItem
                                onClick={() =>
                                    handleDeleteArchive(archive.fileId)
                                }
                            >
                                <Delete />
                                {t("generalSearchView.remove")}
                            </MenuItem>
                        )}
                    </Menu>
                </>
            ) : (
                <>
                    <IconButton
                        component="a"
                        href={
                            hasPlainFile
                                ? webApiGetArchive(archive.fileId)
                                : undefined
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        title={t("tableView.actions.download")}
                        disabled={!hasPlainFile}
                        data-tour="archive-download-button"
                        sx={{
                            "&:hover": {
                                backgroundColor: "action.hover",
                                transform: "scale(1.1)",
                            },
                            transition: "all 0.2s ease-in-out",
                        }}
                    >
                        <Download />
                    </IconButton>
                    <IconButton
                        component="a"
                        href={
                            hasEncryptedFile
                                ? webApiGetArchiveEncrypted(archive.fileId)
                                : undefined
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        title={t("tableView.actions.download_encrypted")}
                        disabled={!hasEncryptedFile}
                        sx={{
                            "&:hover": {
                                backgroundColor: "action.hover",
                                transform: "scale(1.1)",
                            },
                            transition: "all 0.2s ease-in-out",
                        }}
                    >
                        <Lock />
                    </IconButton>
                    <IconButton
                        onClick={() => {
                            showArchiveQuery(archive.fileId);
                        }}
                        title={t("tableView.actions.search")}
                        sx={{
                            "&:hover": {
                                backgroundColor: "action.hover",
                                transform: "scale(1.1)",
                            },
                            transition: "all 0.2s ease-in-out",
                        }}
                    >
                        <Search />
                    </IconButton>
                    {!archive.hidden && (
                        <IconButton
                            onClick={() => handleDeleteArchive(archive.fileId)}
                            title={t("generalSearchView.remove")}
                            sx={{
                                "&:hover": {
                                    backgroundColor: "action.hover",
                                },
                            }}
                        >
                            <Delete />
                        </IconButton>
                    )}
                </>
            )}
        </>
    );
};
