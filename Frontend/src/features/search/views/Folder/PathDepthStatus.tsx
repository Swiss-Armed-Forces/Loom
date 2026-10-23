import { FilterAltOff, Layers } from "@mui/icons-material";
import { Box, IconButton, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";

import { useAppSelector } from "@app/hooks";
import {
    NO_FOLDER_VIEW_LIMITS,
    selectFilteredFolderViewOptions,
    selectFolderViewOptions,
    setFilteredFolderViewOptions,
    setFolderViewOptions,
} from "@app/slices/searchSlice";
import { AppDispatch } from "@app/store";

import { hasAnyLimit } from "./depthLimits";
import type { FolderViewExpansionKey } from "./folderViewState";

interface PathDepthStatusProps {
    expansionKey?: FolderViewExpansionKey;
}

/**
 * One line naming the limits currently shortening this panel's tree.
 *
 * Both limits default to off, so nothing about the feature is on screen until
 * somebody turns one on — at which point a tree that is missing rows needs to
 * say why, and offer one obvious way back to the whole thing.
 */
export const PathDepthStatus = ({
    expansionKey = "global",
}: PathDepthStatusProps) => {
    const { t } = useTranslation();
    const dispatch = useDispatch<AppDispatch>();
    const globalOptions = useAppSelector(selectFolderViewOptions);
    const filteredOptions = useAppSelector(selectFilteredFolderViewOptions);
    const options =
        expansionKey === "filtered" ? filteredOptions : globalOptions;

    if (!hasAnyLimit(options)) return null;

    const parts: string[] = [];
    if (options.pathDepth !== null) {
        parts.push(t("folderView.pathDepthStatus", { n: options.pathDepth }));
    }
    if (options.extractionDepth !== null) {
        parts.push(
            options.extractionDepth === 0
                ? t("folderView.extractionNoneStatus")
                : t("folderView.extractionDepthStatus", {
                      n: options.extractionDepth,
                  }),
        );
    }

    return (
        <Box
            role="status"
            sx={{
                display: "flex",
                alignItems: "center",
                gap: 0.75,
                px: 1,
                py: 0.5,
                borderBottom: "1px solid",
                borderColor: "divider",
                color: "text.secondary",
            }}
        >
            <Layers sx={{ fontSize: "0.9rem" }} />
            <Typography variant="caption" noWrap sx={{ flex: 1, minWidth: 0 }}>
                {parts.join(" · ")}
            </Typography>
            <Tooltip title={t("folderView.resetDepth")}>
                <IconButton
                    size="small"
                    aria-label={t("folderView.resetDepth")}
                    onClick={() =>
                        dispatch(
                            expansionKey === "filtered"
                                ? setFilteredFolderViewOptions(
                                      NO_FOLDER_VIEW_LIMITS,
                                  )
                                : setFolderViewOptions(NO_FOLDER_VIEW_LIMITS),
                        )
                    }
                >
                    <FilterAltOff sx={{ fontSize: "0.85rem" }} />
                </IconButton>
            </Tooltip>
        </Box>
    );
};
