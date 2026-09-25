import { MoreHoriz, UnfoldLess } from "@mui/icons-material";
import { Box, Breadcrumbs, ButtonBase, Link, Tooltip } from "@mui/material";
import { CSSProperties } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectExpandFilePaths,
    selectQuery,
    setExpandFilePaths,
    updateQuery,
} from "@app/slices/searchSlice";
import { SearchQueryField } from "@features/common/utils/enums";
import { updateFieldOfQuery } from "@features/common/utils/helpers";

const MAX_PATH_ITEMS = 4;
const ITEMS_AFTER_COLLAPSE = 3;

interface ClickableFilePathProps {
    fullPath: string;
    style?: CSSProperties;
}

export const ClickableFilePath = ({
    fullPath,
    style,
}: ClickableFilePathProps) => {
    const { t } = useTranslation();
    const searchQuery = useAppSelector(selectQuery);
    const expandFilePaths = useAppSelector(selectExpandFilePaths);
    const dispatch = useAppDispatch();

    const fullPathParts = fullPath.split("/").filter((part) => part !== "");
    const fullPathPartsExtended = fullPathParts.map((part, idx) => {
        return {
            part: part,
            pathToPart: `//${fullPathParts
                .filter((_, innerIdx) => innerIdx <= idx)
                .join("/")}`,
            isLast: idx === fullPathParts.length - 1,
        };
    });

    // Truncation follows the global flag alone. MUI's own Breadcrumbs collapse
    // keeps per-instance state, which would let one card disagree with the
    // rest, so the slicing happens here instead.
    const isTruncatable = fullPathParts.length > MAX_PATH_ITEMS;
    const isTruncated = isTruncatable && !expandFilePaths;
    const visiblePathParts = isTruncated
        ? fullPathPartsExtended.slice(-ITEMS_AFTER_COLLAPSE)
        : fullPathPartsExtended;
    const hiddenPath = isTruncated
        ? `/${fullPathParts.slice(0, -ITEMS_AFTER_COLLAPSE).join("/")}`
        : "";
    const toggleLabel = expandFilePaths
        ? t("resultCard.collapseAllPaths")
        : hiddenPath;

    const lastName = fullPathParts[fullPathParts.length - 1] ?? "";
    const dotIdx = lastName.lastIndexOf(".");
    const fileExtension = dotIdx > 0 ? lastName.slice(dotIdx) : null;
    const fileBaseName = dotIdx > 0 ? lastName.slice(0, dotIdx) : lastName;

    const handleQueryFilterParentPath = (
        newFilepath: string,
        negate: boolean,
        accumulate: boolean,
    ) => {
        const newQuery = updateFieldOfQuery(
            searchQuery?.query ?? "",
            SearchQueryField.ParentPath,
            newFilepath,
            false,
            negate,
            accumulate,
        );
        dispatch(
            updateQuery({
                query: newQuery,
            }),
        );
    };

    const handleQueryFilterExtension = (
        ext: string,
        negate: boolean,
        accumulate: boolean,
    ) => {
        const newQuery = updateFieldOfQuery(
            searchQuery?.query ?? "",
            SearchQueryField.Extension,
            ext,
            false,
            negate,
            accumulate,
        );
        dispatch(updateQuery({ query: newQuery }));
    };

    const handleQueryFilterFilename = (
        name: string,
        negate: boolean,
        accumulate: boolean,
    ) => {
        const newQuery = updateFieldOfQuery(
            searchQuery?.query ?? "",
            SearchQueryField.Filename,
            name,
            false,
            negate,
            accumulate,
        );
        dispatch(updateQuery({ query: newQuery }));
    };

    return (
        <Box sx={{ display: "flex", alignItems: "center" }}>
            <Breadcrumbs
                separator="/"
                sx={{
                    "& .MuiBreadcrumbs-separator": { mx: 0.25 },
                }}
                style={style}
            >
                {/* One control in one place for both directions: it heads the
                    trail where the hidden ancestors would be, so the collapsed
                    state shows that the path continues to the left, and
                    toggling it never moves the control or reflows the row. */}
                {isTruncatable && (
                    <Tooltip title={toggleLabel} placement="top" arrow>
                        <ButtonBase
                            focusRipple
                            aria-label={toggleLabel}
                            onClick={(e) => {
                                e.stopPropagation();
                                dispatch(setExpandFilePaths(!expandFilePaths));
                            }}
                            // The card highlights itself from a bubbling focus
                            // event as well as from clicks. Letting focus
                            // through would not just highlight the card, it
                            // would re-render it between mousedown and mouseup
                            // and swallow the click entirely.
                            onFocus={(e) => e.stopPropagation()}
                            sx={{
                                borderRadius: 1,
                                backgroundColor: "action.selected",
                                color: "inherit",
                                padding: "2px 4px",
                                "&:hover, &:focus": {
                                    backgroundColor: "action.focus",
                                },
                            }}
                        >
                            {expandFilePaths ? (
                                <UnfoldLess
                                    // The path folds horizontally, not
                                    // vertically like the icon assumes.
                                    sx={{
                                        width: 24,
                                        height: 16,
                                        transform: "rotate(90deg)",
                                    }}
                                />
                            ) : (
                                <MoreHoriz sx={{ width: 24, height: 16 }} />
                            )}
                        </ButtonBase>
                    </Tooltip>
                )}
                {visiblePathParts.map((part) => {
                    const isLast = part.isLast;
                    const displayName =
                        isLast && fileExtension ? fileBaseName : part.part;

                    return (
                        <Box
                            key={part.pathToPart}
                            component="span"
                            sx={{ display: "inline" }}
                        >
                            <Tooltip
                                title={
                                    isLast
                                        ? t("resultCard.filterByFilename")
                                        : t("resultCard.filterByParentPath")
                                }
                                placement="top"
                                arrow
                            >
                                <Link
                                    color="inherit"
                                    onClick={(e) => {
                                        if (isLast) {
                                            handleQueryFilterFilename(
                                                fileBaseName,
                                                e.shiftKey,
                                                e.ctrlKey,
                                            );
                                        } else {
                                            handleQueryFilterParentPath(
                                                part.pathToPart,
                                                e.shiftKey,
                                                e.ctrlKey,
                                            );
                                        }
                                    }}
                                    sx={{
                                        cursor: "pointer",
                                        textDecoration: "none",
                                        "&:hover": {
                                            textDecoration: "underline",
                                            color: "secondary.main",
                                        },
                                    }}
                                >
                                    {displayName}
                                </Link>
                            </Tooltip>
                            {isLast && fileExtension && (
                                <Tooltip
                                    title={t("resultCard.filterByExtension")}
                                    placement="top"
                                    arrow
                                >
                                    <Box
                                        component="span"
                                        onClick={(e: React.MouseEvent) => {
                                            e.stopPropagation();
                                            handleQueryFilterExtension(
                                                fileExtension,
                                                e.shiftKey,
                                                e.ctrlKey,
                                            );
                                        }}
                                        sx={{
                                            cursor: "pointer",
                                            textDecoration: "underline dotted",
                                            "&:hover": {
                                                textDecoration: "underline",
                                                color: "secondary.main",
                                            },
                                        }}
                                    >
                                        {fileExtension}
                                    </Box>
                                </Tooltip>
                            )}
                        </Box>
                    );
                })}
            </Breadcrumbs>
        </Box>
    );
};
