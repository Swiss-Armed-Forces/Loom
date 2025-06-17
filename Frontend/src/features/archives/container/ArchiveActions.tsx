import { IconButton, Menu, MenuItem, useMediaQuery } from "@mui/material";
import { useAppDispatch } from "../../../app/hooks";
import { webApiGetArchive, webApiGetArchiveEncrypted } from "../../common/urls";
import { Delete, Download, Search, Lock } from "@mui/icons-material";
import MenuIcon from "@mui/icons-material/Menu";
import { ArchiveHit, hideArchive } from "../../../app/api";
import { updateQuery } from "../../search/searchSlice";
import { removeArchive } from "../archiveSlice";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useState } from "react";

interface ArchiveActions {
    archive: ArchiveHit;
}

export function ArchiveActions({ archive }: ArchiveActions) {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const { t } = useTranslation();
    const matchMedia = useMediaQuery("(max-width: 1300px)");
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

    const handleMenuOpen = (
        event: React.MouseEvent<HTMLButtonElement, MouseEvent>,
    ) => {
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

    const handleHideArchive = async (archiveId: string) => {
        await hideArchive(archiveId);
        dispatch(removeArchive(archiveId));
    };
    return (
        <>
            {matchMedia ? (
                <>
                    <IconButton
                        edge="start"
                        color="inherit"
                        aria-label="menu"
                        onClick={handleMenuOpen}
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
                            href={webApiGetArchive(archive.fileId)}
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            <Download color="secondary" />
                            {t("tableView.actions.download")}
                        </MenuItem>
                        <MenuItem
                            component="a"
                            href={webApiGetArchiveEncrypted(archive.fileId)}
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            <Lock color="secondary" />
                            {t("tableView.actions.download_encrypted")}
                        </MenuItem>
                        <MenuItem
                            onClick={() => showArchiveQuery(archive.fileId)}
                        >
                            <Search color="secondary" />
                            {t("tableView.actions.search")}
                        </MenuItem>
                        {!archive.hidden && (
                            <MenuItem
                                onClick={() =>
                                    handleHideArchive(archive.fileId)
                                }
                            >
                                <Delete color="secondary" />
                                {t("generalSearchView.remove")}
                            </MenuItem>
                        )}
                    </Menu>
                </>
            ) : (
                <>
                    <IconButton
                        component="a"
                        href={webApiGetArchive(archive.fileId)}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={t("tableView.actions.download")}
                    >
                        <Download color="secondary" />
                    </IconButton>
                    <IconButton
                        component="a"
                        href={webApiGetArchiveEncrypted(archive.fileId)}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={t("tableView.actions.download_encrypted")}
                    >
                        <Lock color="secondary" />
                    </IconButton>
                    <IconButton
                        onClick={() => showArchiveQuery(archive.fileId)}
                        title={t("tableView.actions.search")}
                    >
                        <Search color="secondary" />
                    </IconButton>
                    {!archive.hidden && (
                        <IconButton
                            onClick={() => handleHideArchive(archive.fileId)}
                            title={t("generalSearchView.remove")}
                        >
                            <Delete color="secondary" />
                        </IconButton>
                    )}
                </>
            )}
        </>
    );
}
