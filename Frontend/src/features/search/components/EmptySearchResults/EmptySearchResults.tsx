import {
    Alert,
    AlertTitle,
    Box,
    Card,
    CardContent,
    CardHeader,
    Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    updateQuery,
    selectQuery,
    selectQueryError,
} from "@app/slices/searchSlice";

import styles from "./EmptySearchResults.module.css";

export const EmptySearchResults = () => {
    const searchQuery = useAppSelector(selectQuery);
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const queryError = useAppSelector(selectQueryError);

    const performSearch = (
        query: string,
        sortField?: string,
        sortDirection?: "asc" | "desc",
    ) => {
        type SearchParams = {
            query: string;
            sortField?: string;
            sortDirection?: "asc" | "desc" | undefined;
        };
        const searchParams: SearchParams = {
            query: query,
        };

        if (sortField != undefined) {
            searchParams.sortField = sortField;
        }
        if (sortDirection != undefined) {
            searchParams.sortDirection = sortDirection;
        }

        dispatch(updateQuery(searchParams));
    };

    const createSearchTip = (query: string, searchKey: string) => (
        <li>
            <span
                className={styles.clickableSpan}
                onClick={() => {
                    performSearch(query);
                }}
            >
                {query}
            </span>{" "}
            - {t("emptySearch.tips." + searchKey)}
        </li>
    );

    const createHotkey = (keys: string[], searchKey: string) => (
        <li>
            {keys.map((key, i) => (
                <span key={key}>
                    <kbd>{key}</kbd>
                    {i < keys.length - 1 && " / "}
                </span>
            ))}
            - {t("emptySearch.hotkeys." + searchKey)}
        </li>
    );

    return (
        <Box className={styles.emptyCard}>
            {queryError && (
                <Alert severity="error">
                    <AlertTitle>{t("emptySearch.title.queryError")}</AlertTitle>
                    {String(queryError)}
                </Alert>
            )}
            <Card>
                <CardHeader
                    sx={{ pb: 0 }}
                    title={
                        <span className={styles.emptyCardHeaderTitle}>
                            {searchQuery?.query
                                ? t("emptySearch.title.nothingFound")
                                : t("emptySearch.title.default")}
                        </span>
                    }
                />
                <CardContent>
                    <Box>
                        <Box
                            sx={{
                                display: "grid",
                                gridTemplateColumns: "1fr 1fr",
                                gap: 4,
                                alignItems: "start",
                            }}
                        >
                            <Box>
                                <Typography
                                    variant="overline"
                                    color="text.secondary"
                                    sx={{ display: "block", mb: 0.5 }}
                                >
                                    {t("emptySearch.tips.title")}
                                </Typography>
                                <Box
                                    component="ul"
                                    sx={{ m: 0, pl: 2.5, fontSize: "0.85rem" }}
                                >
                                    {createSearchTip("*", "showAll")}
                                    {createSearchTip("John Smith", "keyword")}
                                    {createSearchTip("Jo*", "prefix")}
                                    {createSearchTip("/.*Jo?n.*/", "regex")}
                                    {createSearchTip('"John Smith"', "exact")}
                                    {createSearchTip(
                                        '"John Smith"~10',
                                        "exactDistance",
                                    )}
                                    {createSearchTip("John~2", "fuzzy")}
                                    {createSearchTip(
                                        "filename:*.txt",
                                        "filename",
                                    )}
                                    {createSearchTip("size:>1M", "size")}
                                    {createSearchTip("modified:today", "when")}
                                    {createSearchTip("author:/.*/", "author")}
                                    {createSearchTip(
                                        "tags:interesting",
                                        "tags",
                                    )}
                                    {createSearchTip(
                                        "NOT tags:interesting",
                                        "tagsNegate",
                                    )}
                                    {createSearchTip(
                                        "tags:interesting AND modified:today",
                                        "and",
                                    )}
                                    {createSearchTip(
                                        "tags:interesting OR modified:today",
                                        "or",
                                    )}
                                    {createSearchTip("seen:true", "seen")}
                                    {createSearchTip("flagged:true", "flagged")}
                                    {createSearchTip("hidden:true", "hidden")}
                                    {createSearchTip("hidden:*", "allHidden")}
                                    {createSearchTip(
                                        'file_type:"image/png"',
                                        "fileType",
                                    )}
                                    {createSearchTip(
                                        "uploaded:[* TO 2020-06-15]",
                                        "uploadTime",
                                    )}
                                    {createSearchTip(
                                        "created:{2020-12-31 TO 2025-01-01}",
                                        "creationTime",
                                    )}
                                    {createSearchTip(
                                        "modified:[2021-01-01 TO 2025-01-01}",
                                        "modificationTime",
                                    )}
                                    {createSearchTip("secrets:*", "secrets")}
                                    {createSearchTip(
                                        "source:crawlerX",
                                        "source",
                                    )}
                                    {createSearchTip(
                                        "state:failed",
                                        "stateFailed",
                                    )}
                                    {createSearchTip("summary:*", "summary")}
                                    {createSearchTip("*:John", "allFields")}
                                    {createSearchTip(
                                        "\\*name\\*:*txt*",
                                        "nameFields",
                                    )}
                                </Box>
                                <Typography
                                    variant="overline"
                                    color="text.secondary"
                                    sx={{ display: "block", mt: 2, mb: 0.5 }}
                                >
                                    {t("emptySearch.sort.title")}
                                </Typography>
                                <Box
                                    component="ul"
                                    sx={{ m: 0, pl: 2.5, fontSize: "0.85rem" }}
                                >
                                    <li>
                                        <span
                                            className={styles.clickableSpan}
                                            onClick={() => {
                                                performSearch(
                                                    "*",
                                                    "short_name",
                                                    "asc",
                                                );
                                            }}
                                        >
                                            sort:short_name
                                        </span>{" "}
                                        - {t("emptySearch.sort.name")}
                                    </li>
                                    <li>
                                        <span
                                            className={styles.clickableSpan}
                                            onClick={() => {
                                                performSearch(
                                                    "*",
                                                    "uploaded_datetime",
                                                    "desc",
                                                );
                                            }}
                                        >
                                            sort:uploaded_datetime
                                        </span>{" "}
                                        - {t("emptySearch.sort.uploaded")}
                                    </li>
                                    <li>
                                        <span
                                            className={styles.clickableSpan}
                                            onClick={() => {
                                                performSearch(
                                                    "*",
                                                    "tika_meta.dcterms_created",
                                                    "desc",
                                                );
                                            }}
                                        >
                                            sort:dcterms:created
                                        </span>{" "}
                                        - {t("emptySearch.sort.created")}
                                    </li>
                                </Box>
                                <Typography
                                    variant="body2"
                                    className={styles.clickableSpan}
                                    sx={{ display: "inline-block", mt: 1 }}
                                    onClick={() => {
                                        window.location.assign(
                                            "https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html#query-string-syntax",
                                        );
                                    }}
                                >
                                    {t("emptySearch.advancedGuide")}
                                </Typography>
                            </Box>
                            <Box>
                                <Typography
                                    variant="overline"
                                    color="text.secondary"
                                    sx={{ display: "block", mb: 0.5 }}
                                >
                                    {t("emptySearch.hotkeys.title")}
                                </Typography>
                                <Box
                                    component="ul"
                                    sx={{ m: 0, pl: 2.5, fontSize: "0.85rem" }}
                                >
                                    {createHotkey(["j", "↓"], "moveDown")}
                                    {createHotkey(["k", "↑"], "moveUp")}
                                    {createHotkey(
                                        ["Enter", "Space", "i"],
                                        "openDetails",
                                    )}
                                    {createHotkey(
                                        ["Ctrl + click"],
                                        "openDetailsBackground",
                                    )}
                                    {createHotkey(
                                        ["Shift + click"],
                                        "shiftClickNegate",
                                    )}
                                    {createHotkey(["Escape"], "clear")}
                                    {createHotkey(["/"], "search")}
                                    {createHotkey(["g"], "flag")}
                                    {createHotkey(["b"], "see")}
                                    {createHotkey(["c"], "share")}
                                    {createHotkey(["d"], "download")}
                                    {createHotkey(["r"], "reindex")}
                                    {createHotkey(["s"], "summarize")}
                                    {createHotkey(["t"], "addTags")}
                                    {createHotkey(["Shift + t"], "translate")}
                                </Box>
                                <Typography
                                    variant="overline"
                                    color="text.secondary"
                                    sx={{ display: "block", mt: 2, mb: 0.5 }}
                                >
                                    {t("emptySearch.hotkeys.detailsTitle")}
                                </Typography>
                                <Box
                                    component="ul"
                                    sx={{ m: 0, pl: 2.5, fontSize: "0.85rem" }}
                                >
                                    {createHotkey(["h", "←"], "previousTab")}
                                    {createHotkey(["l", "→"], "nextTab")}
                                    {createHotkey(["f"], "fullscreen")}
                                    {createHotkey(
                                        ["Escape", "Enter", "Space", "i"],
                                        "close",
                                    )}
                                </Box>
                            </Box>
                        </Box>
                    </Box>
                </CardContent>
            </Card>
        </Box>
    );
};
