import { UnfoldLess } from "@mui/icons-material";
import { Box, Breadcrumbs, IconButton, Link, Tooltip } from "@mui/material";
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
        };
    });

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
        <Box
            sx={{ display: "flex", alignItems: "center" }}
            onClick={(e: React.MouseEvent) => {
                if (
                    !expandFilePaths &&
                    (e.target as Element).closest("button")
                ) {
                    e.stopPropagation();
                    dispatch(setExpandFilePaths(true));
                }
            }}
        >
            {expandFilePaths && fullPathParts.length > MAX_PATH_ITEMS && (
                <IconButton
                    size="small"
                    onClick={(e) => {
                        e.stopPropagation();
                        dispatch(setExpandFilePaths(false));
                    }}
                    title="Collapse all paths"
                    sx={{ mr: 0.5, borderRadius: 1 }}
                >
                    <UnfoldLess fontSize="small" />
                </IconButton>
            )}
            <Breadcrumbs
                key={String(expandFilePaths)}
                separator="/"
                sx={{
                    "& .MuiBreadcrumbs-separator": { mx: 0.25 },
                    "& button": {
                        borderRadius: 1,
                        backgroundColor: "action.selected",
                        padding: "2px 4px",
                    },
                }}
                maxItems={expandFilePaths ? undefined : MAX_PATH_ITEMS}
                itemsBeforeCollapse={0}
                itemsAfterCollapse={3}
                style={style}
            >
                {fullPathPartsExtended.map((part, idx) => {
                    const isLast = idx === fullPathPartsExtended.length - 1;
                    const displayName =
                        isLast && fileExtension ? fileBaseName : part.part;

                    return (
                        <Box
                            key={idx}
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
