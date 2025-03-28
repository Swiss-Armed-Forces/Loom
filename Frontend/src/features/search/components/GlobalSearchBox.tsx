import { ArrowDownward, ArrowUpward, Search, Sort } from "@mui/icons-material";
import { IconButton, InputBase, styled } from "@mui/material";
import { ChangeEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";

import { selectQuery, updateQuery } from "../searchSlice";
import styles from "./GlobalSearchBox.module.css";
import { SearchTranslateDialog } from "./SearchTranslateDialog";

const StyledInputBase = styled(InputBase)(() => ({
    color: "inherit",
    borderRadius: "0.3rem",
    backgroundColor: "rgba(0, 0, 0, 0.15)",
    transition: "background-color 0.5s ease",
    ":hover": {
        backgroundColor: "rgba(0, 0, 0, 0.25)",
    },
}));

export function GlobalSearchBox() {
    const searchQuery = useAppSelector(selectQuery);
    const [searchInputFieldContent, setSearchInputFieldContent] =
        useState<string>("");
    const [sortInputFieldContent, setSortInputFieldContent] =
        useState<string>("");
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
    const dispatch = useAppDispatch();
    const { t } = useTranslation();

    useEffect(() => {
        if (!searchQuery) return;
        setSearchInputFieldContent(searchQuery.query ?? "");
        setSortInputFieldContent(searchQuery.sortField ?? "");
        setSortDirection(searchQuery.sortDirection ?? "desc");
    }, [searchQuery]);

    const doUpdateQuery = () => {
        dispatch(
            updateQuery({
                query: searchInputFieldContent,
                sortField: sortInputFieldContent,
                sortDirection: sortDirection,
            }),
        );
        window.location.hash = "";
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
        <div className={styles.globalSearchBox}>
            <StyledInputBase
                startAdornment={<Search sx={{ p: 1 }} />}
                endAdornment={<SearchTranslateDialog />}
                placeholder={t("globalSearchBox.searchPlaceholder")}
                inputProps={{ "aria-label": "search" }}
                value={searchInputFieldContent ?? ""}
                onChange={handleSearchValueChange}
                onKeyDown={(ev: React.KeyboardEvent<HTMLInputElement>) => {
                    if (ev.key === "Enter") {
                        ev.preventDefault();
                        doUpdateQuery();
                    }
                }}
            />
            <StyledInputBase
                startAdornment={<Sort sx={{ p: 1 }} />}
                endAdornment={
                    <IconButton
                        color="inherit"
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
    );
}
