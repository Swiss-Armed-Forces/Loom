import { Download } from "@mui/icons-material";
import { IconButton, Menu, MenuItem } from "@mui/material";
import React from "react";
import { webApiGetFile, webApiGetFileText } from "../urls";
import { useTranslation } from "react-i18next";
import { OverridableStringUnion } from "@mui/types";

interface IconButtonDownloadMenuProps {
    fileId: string;
    iconColor?: OverridableStringUnion<
        | "inherit"
        | "action"
        | "disabled"
        | "primary"
        | "secondary"
        | "error"
        | "info"
        | "success"
        | "warning"
    >;
}

export function IconButtonDownloadMenu({
    fileId,
    iconColor,
}: IconButtonDownloadMenuProps) {
    const { t } = useTranslation();
    const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>();
    const openDownloadMenu = Boolean(anchorEl);

    const clickDownloadMenuOpener = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const closeDownloadMenu = () => {
        setAnchorEl(null);
    };

    return (
        <>
            <IconButton
                title="Download"
                aria-controls={
                    openDownloadMenu ? fileId + "-download-menu" : undefined
                }
                aria-haspopup="true"
                aria-expanded={openDownloadMenu ? "true" : undefined}
                aria-label="download"
                onClick={clickDownloadMenuOpener}
            >
                <Download color={iconColor ? iconColor : undefined} />
            </IconButton>
            <Menu
                id={fileId + "-download-menu"}
                anchorEl={anchorEl}
                open={openDownloadMenu}
                onClose={closeDownloadMenu}
            >
                <MenuItem
                    component="a"
                    href={webApiGetFile(fileId)}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    {t("downloadOptions.originalFile")}
                </MenuItem>
                <MenuItem
                    component="a"
                    href={webApiGetFileText(fileId)}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    {t("downloadOptions.contentOriginal")}
                </MenuItem>
            </Menu>
        </>
    );
}
