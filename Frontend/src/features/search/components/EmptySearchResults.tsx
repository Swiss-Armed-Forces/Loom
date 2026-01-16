import styles from "./EmptySearchResults.module.css";
import Card from "@mui/material/Card";
import CardHeader from "@mui/material/CardHeader";
import CardContent from "@mui/material/CardContent";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { updateQuery, selectQuery, selectQueryError } from "../searchSlice";
import { useTranslation } from "react-i18next";
import { Alert, AlertTitle, Box } from "@mui/material";

export function EmptySearchResults() {
    const searchQuery = useAppSelector(selectQuery);
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const queryError = useAppSelector(selectQueryError);

    const performSearch = (
        query: string,
        sortField?: string,
        sortDirection?: "asc" | "desc" | undefined,
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
                    className={styles.emptyCardTitle}
                    title={
                        <span className={styles.emptyCardHeaderTitle}>
                            {searchQuery?.query
                                ? t("emptySearch.title.nothingFound")
                                : t("emptySearch.title.default")}
                        </span>
                    }
                />
                <CardContent>
                    <div>
                        <p style={{ marginTop: 0 }}>
                            {t("emptySearch.description")}
                        </p>
                        <div>
                            <p>{t("emptySearch.tips.title")}</p>
                            <ul>
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
                                {createSearchTip("filename:*.txt", "filename")}
                                {createSearchTip("size:>1M", "size")}
                                {createSearchTip("modified:today", "when")}
                                {createSearchTip("author:/.*/", "author")}
                                {createSearchTip("tags:interesting", "tags")}
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
                                {createSearchTip("hidden:true", "hidden")}
                                {createSearchTip("hidden:*", "allHidden")}
                                {createSearchTip(
                                    "file_type:image/png",
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
                                {createSearchTip("*:John", "allFields")}
                                {createSearchTip(
                                    "\\*name\\*:*txt*",
                                    "nameFields",
                                )}
                            </ul>
                        </div>
                        <div>
                            <p>{t("emptySearch.sort.title")}</p>
                            <ul>
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
                                                "tika_meta.dcterms:created",
                                                "desc",
                                            );
                                        }}
                                    >
                                        sort:dcterms:created
                                    </span>{" "}
                                    - {t("emptySearch.sort.created")}
                                </li>
                            </ul>
                        </div>
                        <div>
                            <span
                                className={styles.clickableSpan}
                                onClick={() => {
                                    window.location.assign(
                                        "https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html#query-string-syntax",
                                    );
                                }}
                            >
                                {t("emptySearch.advancedGuide")}
                            </span>
                            <p>{t("emptySearch.chatbotGuide")} </p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </Box>
    );
}
