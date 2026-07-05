import { UnfoldLess } from "@mui/icons-material";
import { Box, Breadcrumbs, IconButton, Link } from "@mui/material";
import { CSSProperties } from "react";

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

    const handleQueryReplaceFilename = (
        newFilepath: string,
        negate: boolean,
    ) => {
        const newQuery = updateFieldOfQuery(
            searchQuery?.query ?? "",
            SearchQueryField.Filename,
            newFilepath,
            false,
            negate,
        );
        dispatch(
            updateQuery({
                query: newQuery,
            }),
        );
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
                {fullPathPartsExtended.map((part, idx) => (
                    <Link
                        key={idx}
                        color="inherit"
                        onClick={(e) => {
                            handleQueryReplaceFilename(
                                part.pathToPart,
                                e.shiftKey,
                            );
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
                        {part.part}
                    </Link>
                ))}
            </Breadcrumbs>
        </Box>
    );
};
