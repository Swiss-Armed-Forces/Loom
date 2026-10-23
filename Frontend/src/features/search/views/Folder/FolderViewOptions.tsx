import { Close, Tune } from "@mui/icons-material";
import {
    Box,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    Popover,
    Slider,
    Tooltip,
    Typography,
    useMediaQuery,
} from "@mui/material";
import { ReactNode, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";

import { getTreeDepthLimits } from "@app/api";
import { useAppSelector } from "@app/hooks";
import {
    FolderViewOptions as FolderViewOptionsValue,
    NO_FOLDER_VIEW_LIMITS,
    selectFilteredFolderViewOptions,
    selectFolderViewOptions,
    selectQuery,
    setFilteredFolderViewOptions,
    setFolderViewOptions,
} from "@app/slices/searchSlice";
import { AppDispatch } from "@app/store";

import { hasAnyLimit } from "./depthLimits";
import type { FolderViewExpansionKey } from "./folderViewState";

/** How deep the indexed data actually goes, on each axis.
 *
 *  Sliders are drawn from 0 to these, so neither offers a setting the corpus
 *  cannot show a difference at. Until the answer arrives there is nothing
 *  truthful to draw a scale against. */
interface DepthCeilings {
    path: number;
    extraction: number;
}

interface DepthSliderProps {
    label: string;
    help: string;
    /** Top of the scale, which is also the "no limit" end. */
    max: number;
    value: number | null;
    onChange: (value: number | null) => void;
    /** Label for 0, where it reads as "none of it" rather than as a count. */
    zeroLabel?: string;
    unlimitedLabel: string;
}

const DepthSlider = ({
    label,
    help,
    max,
    value,
    onChange,
    zeroLabel,
    unlimitedLabel,
}: DepthSliderProps) => {
    const labelId = `path-depth-${label.replace(/\s+/g, "-").toLowerCase()}`;
    // The top of the scale is "no limit": a limit equal to the deepest the data
    // goes hides nothing, so storing it as a number would only make the setting
    // go stale the moment a deeper file is indexed.
    const sliderValue = value ?? max;
    const readout =
        value === null
            ? unlimitedLabel
            : value === 0 && zeroLabel
              ? zeroLabel
              : String(value);

    return (
        <Box sx={{ display: "grid", gap: 0.25 }}>
            <Box
                sx={{
                    display: "flex",
                    alignItems: "baseline",
                    gap: 1,
                }}
            >
                <Typography variant="subtitle2" id={labelId} sx={{ flex: 1 }}>
                    {label}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    {readout}
                </Typography>
            </Box>
            <Slider
                size="small"
                min={0}
                max={max}
                step={1}
                marks
                value={sliderValue}
                aria-labelledby={labelId}
                valueLabelDisplay="auto"
                valueLabelFormat={(shown: number) =>
                    shown === max
                        ? unlimitedLabel
                        : shown === 0 && zeroLabel
                          ? zeroLabel
                          : String(shown)
                }
                onChange={(_, next) => {
                    const picked = Array.isArray(next) ? next[0] : next;
                    onChange(picked >= max ? null : picked);
                }}
            />
            <Typography variant="caption" color="text.secondary">
                {help}
            </Typography>
        </Box>
    );
};

interface FolderViewOptionsButtonProps {
    expansionKey?: FolderViewExpansionKey;
}

/**
 * The folder panel's view options: the two depth limits, per panel.
 *
 * A Popover rather than the Menu every other anchored surface in this app uses,
 * because a Menu carries list semantics and the shared j/k handler, neither of
 * which fits a pair of sliders. Below the app's mobile breakpoint it becomes a
 * full-screen Dialog, as every dialog here already does.
 */
export const FolderViewOptionsButton = ({
    expansionKey = "global",
}: FolderViewOptionsButtonProps) => {
    const { t } = useTranslation();
    const dispatch = useDispatch<AppDispatch>();
    const isMobile = useMediaQuery("(max-width:600px)");
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [ceilings, setCeilings] = useState<DepthCeilings | null>(null);

    const searchQuery = useAppSelector(selectQuery);
    const globalOptions = useAppSelector(selectFolderViewOptions);
    const filteredOptions = useAppSelector(selectFilteredFolderViewOptions);
    const options =
        expansionKey === "filtered" ? filteredOptions : globalOptions;

    const isOpen = Boolean(anchorEl);

    // Asked for when the surface opens rather than on mount: it is one
    // aggregation over the whole result set, and nothing reads the answer until
    // there is a scale on screen to draw.
    useEffect(() => {
        if (!isOpen || !searchQuery) return;
        let cancelled = false;
        getTreeDepthLimits(searchQuery)
            .then((limits) => {
                if (cancelled) return;
                setCeilings({
                    path: limits.maxPathDepth,
                    extraction: limits.maxExtractionDepth,
                });
            })
            .catch(() => {
                if (!cancelled) setCeilings(null);
            });
        return () => {
            cancelled = true;
        };
    }, [isOpen, searchQuery]);

    const apply = (next: FolderViewOptionsValue) =>
        dispatch(
            expansionKey === "filtered"
                ? setFilteredFolderViewOptions(next)
                : setFolderViewOptions(next),
        );

    const close = () => setAnchorEl(null);

    // Every other anchored surface in the app closes on this, and the keyboard
    // navigation fires it on each highlight move — so without it this one would
    // hang over a sidebar that has scrolled out from under it.
    useEffect(() => {
        const onCloseMenus = () => setAnchorEl(null);
        document.addEventListener("loom:close-menus", onCloseMenus);
        return () =>
            document.removeEventListener("loom:close-menus", onCloseMenus);
    }, []);

    const controls: ReactNode =
        ceilings === null ? (
            <Typography variant="caption" color="text.secondary">
                {t("folderView.depthLimitsLoading")}
            </Typography>
        ) : (
            <Box sx={{ display: "grid", gap: isMobile ? 2.5 : 1.75 }}>
                {ceilings.path > 0 && (
                    <DepthSlider
                        label={t("folderView.pathDepthLabel")}
                        help={t("folderView.pathDepthHelp")}
                        max={ceilings.path}
                        value={options.pathDepth}
                        onChange={(pathDepth) =>
                            apply({ ...options, pathDepth })
                        }
                        unlimitedLabel={t("folderView.depthAll")}
                    />
                )}
                {ceilings.extraction > 0 && (
                    <DepthSlider
                        label={t("folderView.extractionDepthLabel")}
                        help={t("folderView.extractionDepthHelp")}
                        max={ceilings.extraction}
                        value={options.extractionDepth}
                        onChange={(extractionDepth) =>
                            apply({ ...options, extractionDepth })
                        }
                        zeroLabel={t("folderView.extractionNone")}
                        unlimitedLabel={t("folderView.depthAll")}
                    />
                )}
                {/* A corpus with nothing nested on either axis has no limit
                    worth offering, and an empty popover needs to say so. */}
                {ceilings.path === 0 && ceilings.extraction === 0 && (
                    <Typography variant="caption" color="text.secondary">
                        {t("folderView.depthLimitsUnavailable")}
                    </Typography>
                )}
            </Box>
        );

    const button = (
        <Tooltip title={t("folderView.viewOptions")}>
            <IconButton
                size="small"
                onClick={(event) => setAnchorEl(event.currentTarget)}
                aria-label={t("folderView.viewOptions")}
                color={hasAnyLimit(options) ? "primary" : "default"}
            >
                <Tune fontSize="small" />
            </IconButton>
        </Tooltip>
    );

    if (isMobile) {
        return (
            <>
                {button}
                <Dialog open={isOpen} onClose={close} fullScreen>
                    <DialogTitle
                        sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                        }}
                    >
                        <Box sx={{ flex: 1 }}>
                            {t("folderView.viewOptions")}
                        </Box>
                        <IconButton
                            size="small"
                            onClick={close}
                            aria-label={t("common.close")}
                        >
                            <Close fontSize="small" />
                        </IconButton>
                    </DialogTitle>
                    <DialogContent>{controls}</DialogContent>
                    <DialogActions>
                        <Button onClick={() => apply(NO_FOLDER_VIEW_LIMITS)}>
                            {t("folderView.resetDepth")}
                        </Button>
                        <Button variant="contained" onClick={close}>
                            {t("common.done")}
                        </Button>
                    </DialogActions>
                </Dialog>
            </>
        );
    }

    return (
        <>
            {button}
            <Popover
                open={isOpen}
                anchorEl={anchorEl}
                onClose={close}
                anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
                transformOrigin={{ vertical: "top", horizontal: "right" }}
                slotProps={{ paper: { sx: { p: 1.75, width: 272 } } }}
                // The result-list shortcuts live on the document, and a slider
                // is not an input, so without this `j` and `k` would move the
                // highlight behind the open surface.
                onKeyDown={(event) => event.stopPropagation()}
            >
                <Box sx={{ display: "grid", gap: 1.5 }}>
                    {controls}
                    <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
                        <Button
                            size="small"
                            disabled={!hasAnyLimit(options)}
                            onClick={() => apply(NO_FOLDER_VIEW_LIMITS)}
                        >
                            {t("folderView.resetDepth")}
                        </Button>
                    </Box>
                </Box>
            </Popover>
        </>
    );
};
