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
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch("*");
                                        }}
                                    >
                                        *
                                    </span>{" "}
                                    - {t("emptySearch.tips.showAll")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch("John Smith");
                                        }}
                                    >
                                        John Smith
                                    </span>{" "}
                                    - {t("emptySearch.tips.keyword")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch("Jo*");
                                        }}
                                    >
                                        Jo&#42;
                                    </span>{" "}
                                    - {t("emptySearch.tips.prefix")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch('"John Smith"');
                                        }}
                                    >
                                        &quot;John Smith&quot;
                                    </span>{" "}
                                    - {t("emptySearch.tips.exact")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch('"John Smith"~10');
                                        }}
                                    >
                                        &quot;John Smith&quot;~10
                                    </span>{" "}
                                    - {t("emptySearch.tips.exactDistance")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch("John~2");
                                        }}
                                    >
                                        John~2
                                    </span>{" "}
                                    - {t("emptySearch.tips.fuzzy")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch("filename:*.txt");
                                        }}
                                    >
                                        filename:*.txt
                                    </span>{" "}
                                    - {t("emptySearch.tips.filename")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch("size:>1M");
                                        }}
                                    >
                                        size:&gt;1M
                                    </span>{" "}
                                    -{t("emptySearch.tips.size")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch("when:today");
                                        }}
                                    >
                                        when:today
                                    </span>{" "}
                                    - {t("emptySearch.tips.when")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch("author:*");
                                        }}
                                    >
                                        author:*
                                    </span>{" "}
                                    - {t("emptySearch.tips.author")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch("tags:interesting");
                                        }}
                                    >
                                        tags:interesting
                                    </span>{" "}
                                    - {t("emptySearch.tips.tags")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch(
                                                "NOT tags:interesting",
                                            );
                                        }}
                                    >
                                        NOT tags:interesting
                                    </span>{" "}
                                    - {t("emptySearch.tips.tagsNegate")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch("hidden:true");
                                        }}
                                    >
                                        hidden:true
                                    </span>{" "}
                                    - {t("emptySearch.tips.removed")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch(
                                                "file_type:image/png",
                                            );
                                        }}
                                    >
                                        file_type:image/png
                                    </span>{" "}
                                    - {t("emptySearch.tips.fileType")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch(
                                                "tags:interesting AND when:today",
                                            );
                                        }}
                                    >
                                        tags:interesting AND when:today
                                    </span>{" "}
                                    - {t("emptySearch.tips.and")}
                                </li>
                                <li>
                                    <span
                                        className={styles.clickableSpan}
                                        onClick={() => {
                                            performSearch(
                                                "tags:interesting OR when:today",
                                            );
                                        }}
                                    >
                                        tags:interesting OR when:today
                                    </span>{" "}
                                    - {t("emptySearch.tips.or")}
                                </li>
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
