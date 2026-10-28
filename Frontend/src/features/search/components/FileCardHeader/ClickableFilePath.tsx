import { MoreHoriz, UnfoldLess } from "@mui/icons-material";
import { Box, Breadcrumbs, ButtonBase, Link } from "@mui/material";
import { CSSProperties } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectExpandFilePaths,
    selectQuery,
    setExpandFilePaths,
    updateQuery,
} from "@app/slices/searchSlice";
import { LazyTooltip } from "@features/common/components";
import { SearchQueryField } from "@features/common/utils/enums";
import { updateFieldOfQuery } from "@features/common/utils/helpers";

const MAX_PATH_ITEMS = 4;
const ITEMS_AFTER_COLLAPSE = 3;
// Omitting maxItems does not disable MUI's own collapse, it defaults it to 8:
// past that, an expanded path was folded back to the toggle and the filename
// and grew a second ellipsis beside ours, driven by state the global flag
// cannot see. The cap has to be set, and out of reach. Not Infinity - the prop
// is validated as an integer.
const NEVER_COLLAPSE = Number.MAX_SAFE_INTEGER;

interface ClickableFilePathProps {
    fullPath: string;
    style?: CSSProperties;
}

// Hoisted out of the render body: three of these sit inside the per-segment
// map, so a four-segment path re-hashed a dozen objects on every card render.
const ROOT_SX = { display: "flex", alignItems: "center" } as const;
const BREADCRUMBS_SX = {
    "& .MuiBreadcrumbs-separator": { mx: 0.25 },
} as const;
const TOGGLE_SX = {
    borderRadius: 1,
    backgroundColor: "action.selected",
    color: "inherit",
    padding: "2px 4px",
    "&:hover, &:focus": { backgroundColor: "action.focus" },
} as const;
const FOLD_ICON_SX = {
    width: 24,
    height: 16,
    transform: "rotate(90deg)",
} as const;
const ELLIPSIS_ICON_SX = { width: 24, height: 16 } as const;
const INLINE_SX = { display: "inline" } as const;
const SEGMENT_SX = {
    cursor: "pointer",
    textDecoration: "none",
    "&:hover": { textDecoration: "underline", color: "secondary.main" },
} as const;
const EXTENSION_SX = {
    cursor: "pointer",
    textDecoration: "underline dotted",
    "&:hover": { textDecoration: "underline", color: "secondary.main" },
} as const;

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
        <Box sx={ROOT_SX}>
            <Breadcrumbs
                separator="/"
                maxItems={NEVER_COLLAPSE}
                sx={BREADCRUMBS_SX}
                style={style}
            >
                {/* One control in one place for both directions: it heads the
                    trail where the hidden ancestors would be, so the collapsed
                    state shows that the path continues to the left, and
                    toggling it never moves the control or reflows the row. */}
                {isTruncatable && (
                    <LazyTooltip title={toggleLabel} placement="top" arrow>
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
                            sx={TOGGLE_SX}
                        >
                            {expandFilePaths ? (
                                <UnfoldLess
                                    // The path folds horizontally, not
                                    // vertically like the icon assumes.
                                    sx={FOLD_ICON_SX}
                                />
                            ) : (
                                <MoreHoriz sx={ELLIPSIS_ICON_SX} />
                            )}
                        </ButtonBase>
                    </LazyTooltip>
                )}
                {visiblePathParts.map((part) => {
                    const isLast = part.isLast;
                    const displayName =
                        isLast && fileExtension ? fileBaseName : part.part;

                    return (
                        <Box
                            key={part.pathToPart}
                            component="span"
                            sx={INLINE_SX}
                        >
                            <LazyTooltip
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
                                    sx={SEGMENT_SX}
                                >
                                    {displayName}
                                </Link>
                            </LazyTooltip>
                            {isLast && fileExtension && (
                                <LazyTooltip
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
                                        sx={EXTENSION_SX}
                                    >
                                        {fileExtension}
                                    </Box>
                                </LazyTooltip>
                            )}
                        </Box>
                    );
                })}
            </Breadcrumbs>
        </Box>
    );
};
