import {
    ArrowDownward,
    ArrowUpward,
    Clear,
    Search,
    Sort,
} from "@mui/icons-material";
import { Chip, IconButton, InputBase, styled } from "@mui/material";
import { ChangeEvent, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectCurrentResultRank,
    selectQuery,
    selectTotalFiles,
    updateQuery,
} from "@app/slices/searchSlice";
import { formatCompactNumber } from "@features/common/utils/helpers";

import styles from "./GlobalSearchBox.module.css";

/*
 * A chip, light on dark, with fixed colours rather than theme tokens.
 *
 * `StyledInputBase` paints its own near-black ground in both colour schemes,
 * so anything that follows the scheme - bare `text.secondary`, a default Chip
 * - comes out black on black in light mode. `inherit` takes the header's own
 * light text, which is what the input next to it does.
 */
const RESULT_COUNT_SX = {
    height: "1.25rem",
    fontSize: "0.7rem",
    mr: 0.5,
    color: "inherit",
    backgroundColor: "rgba(255, 255, 255, 0.16)",
    "& .MuiChip-label": { px: 0.75 },
} as const;

const StyledInputBase = styled(InputBase)(() => ({
    width: "100%",
    minWidth: 0,
    color: "inherit",
    borderRadius: "0.3rem",
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    ":hover": {
        backgroundColor: "rgba(0, 0, 0, 0.85)",
    },
}));

export const GlobalSearchBox = () => {
    const searchQuery = useAppSelector(selectQuery);
    const totalFiles = useAppSelector(selectTotalFiles);
    const currentRank = useAppSelector(selectCurrentResultRank);
    const [searchInputFieldContent, setSearchInputFieldContent] =
        useState<string>("");
    const [sortInputFieldContent, setSortInputFieldContent] =
        useState<string>("");
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const searchInputRef = useRef<HTMLInputElement>(null);
    const [sortVisible, setSortVisible] = useState(false);

    useEffect(() => {
        if (!searchQuery) return;
        setSearchInputFieldContent(searchQuery.query ?? "");
        setSortInputFieldContent(searchQuery.sortField ?? "");
        setSortDirection(searchQuery.sortDirection ?? "desc");
        if (searchQuery.sortField || searchQuery.sortDirection === "asc") {
            setSortVisible(true);
        }
    }, [searchQuery]);

    const doUpdateQuery = () => {
        dispatch(
            updateQuery({
                query: searchInputFieldContent,
                sortField: sortInputFieldContent ? sortInputFieldContent : null,
                sortDirection: sortDirection,
            }),
        );
    };

    const handleSearchValueChange = (
        e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    ) => {
        setSearchInputFieldContent(e.target.value);
    };

    const handleSortValueChange = (
        e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    ) => {
        setSortInputFieldContent(e.target.value);
    };

    const handleClearSearch = () => {
        setSearchInputFieldContent("");
        dispatch(
            updateQuery({
                query: "",
                sortField: sortInputFieldContent ? sortInputFieldContent : null,
                sortDirection: sortDirection,
            }),
        );
    };

    const handleClearSort = () => {
        setSortInputFieldContent("");
        dispatch(
            updateQuery({
                query: searchInputFieldContent,
                sortField: null,
                sortDirection: sortDirection,
            }),
        );
    };

    const handleToggleSortDirection = () => {
        dispatch(
            updateQuery({
                ...(sortDirection && {
                    sortDirection: sortDirection === "desc" ? "asc" : "desc",
                }),
            }),
        );
    };

    return (
        <div
            className={`${styles.globalSearchBox}${sortVisible ? ` ${styles.sortVisible}` : ""}`}
            data-tour="global-search"
        >
            <StyledInputBase
                inputRef={searchInputRef}
                startAdornment={<Search sx={{ p: 1 }} />}
                endAdornment={
                    <>
                        {/* How much the query found, and where in it the
                        reader is. */}
                        {totalFiles > 0 && (
                            <Chip
                                size="small"
                                label={
                                    currentRank === null
                                        ? formatCompactNumber(totalFiles)
                                        : `${formatCompactNumber(currentRank)}/${formatCompactNumber(totalFiles)}`
                                }
                                sx={RESULT_COUNT_SX}
                            />
                        )}
                        {searchInputFieldContent ? (
                            <IconButton
                                color="inherit"
                                size="small"
                                onClick={handleClearSearch}
                                aria-label="clear search"
                            >
                                <Clear fontSize="small" />
                            </IconButton>
                        ) : null}
                        <IconButton
                            color="inherit"
                            size="small"
                            onClick={() => setSortVisible((v) => !v)}
                            aria-label="toggle sort"
                        >
                            <Sort fontSize="small" />
                        </IconButton>
                    </>
                }
                placeholder={t("globalSearchBox.searchPlaceholder")}
                inputProps={{
                    "aria-label": "search",
                    "data-search-input": true,
                }}
                value={searchInputFieldContent ?? ""}
                onChange={handleSearchValueChange}
                onKeyDown={(ev: React.KeyboardEvent<HTMLInputElement>) => {
                    if (ev.key === "Enter") {
                        ev.preventDefault();
                        doUpdateQuery();
                        searchInputRef.current?.blur();
                    } else if (ev.key === "Escape") {
                        ev.preventDefault();
                        searchInputRef.current?.blur();
                    }
                }}
            />
            <div
                className={`${styles.sortInputWrapper}${sortVisible ? ` ${styles.visible}` : ""}`}
            >
                <StyledInputBase
                    startAdornment={<Sort sx={{ p: 1 }} />}
                    endAdornment={
                        <>
                            {sortInputFieldContent ? (
                                <IconButton
                                    color="inherit"
                                    size="small"
                                    onClick={handleClearSort}
                                    aria-label="clear sort"
                                >
                                    <Clear fontSize="small" />
                                </IconButton>
                            ) : null}
                            <IconButton
                                color="inherit"
                                size="small"
                                onClick={(ev) => {
                                    ev.preventDefault();
                                    handleToggleSortDirection();
                                }}
                            >
                                {sortDirection === "asc" ? (
                                    <ArrowUpward />
                                ) : (
                                    <ArrowDownward />
                                )}
                            </IconButton>
                        </>
                    }
                    placeholder={t("globalSearchBox.sortPlaceholder")}
                    inputProps={{ "aria-label": "sort" }}
                    value={sortInputFieldContent ?? ""}
                    onChange={handleSortValueChange}
                    onKeyDown={(ev: React.KeyboardEvent<HTMLInputElement>) => {
                        if (ev.key === "Enter") {
                            ev.preventDefault();
                            doUpdateQuery();
                        }
                    }}
                />
            </div>
        </div>
    );
};
