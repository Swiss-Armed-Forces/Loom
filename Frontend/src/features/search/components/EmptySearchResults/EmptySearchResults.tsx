import {
    Alert,
    AlertTitle,
    Box,
    Card,
    CardContent,
    CardHeader,
    Table,
    TableBody,
    TableCell,
    TableRow,
    Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    updateQuery,
    selectQuery,
    selectQueryError,
} from "@app/slices/searchSlice";
import { selectResolvedBindings } from "@app/slices/searchSlice";
import { shortcutRegistry } from "@features/search/hooks/shortcutRegistry";

import KeyRecorder from "../KeyRecorder/KeyRecorder";

import styles from "./EmptySearchResults.module.css";
import { SEARCH_TIPS } from "./searchTips";

const searchChipSx = {
    display: "inline-block",
    fontFamily: "monospace",
    fontSize: "0.82em",
    bgcolor: "#f0f4ff",
    border: "1px solid #c5cae9",
    borderRadius: 0.5,
    px: 0.6,
    color: "#3949ab",
    cursor: "pointer",
    verticalAlign: "baseline",
    "&:hover": { bgcolor: "#e8eaf6", borderColor: "#5c6bc0" },
    "&:active": { bgcolor: "#c5cae9" },
} as const;

const sortChipSx = {
    display: "inline-block",
    fontFamily: "monospace",
    fontSize: "0.82em",
    bgcolor: "#fffde7",
    border: "1px solid #ffe082",
    borderRadius: 0.5,
    px: 0.6,
    color: "#e65100",
    cursor: "pointer",
    verticalAlign: "baseline",
    "&:hover": { bgcolor: "#fff9c4", borderColor: "#ffd54f" },
    "&:active": { bgcolor: "#fff176" },
} as const;

interface EmptySearchResultsProps {
    forceQueryOverview?: boolean;
}

export const EmptySearchResults = ({
    forceQueryOverview = false,
}: EmptySearchResultsProps) => {
    const searchQuery = useAppSelector(selectQuery);
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const resolvedBindings = useAppSelector(selectResolvedBindings);
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
        <li
            key={query}
            data-tour={query === "*" ? "search-all-query" : undefined}
        >
            <Box
                component="span"
                sx={searchChipSx}
                onClick={() => performSearch(query)}
            >
                {query}
            </Box>{" "}
            - {t("emptySearch.tips." + searchKey)}
        </li>
    );

    return (
        <Box className={styles.emptyCard}>
            {!forceQueryOverview && queryError && (
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
                            {searchQuery?.query && !forceQueryOverview
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
                                gridTemplateColumns: {
                                    xs: "1fr",
                                    sm: "1fr 1fr",
                                },
                                gap: { xs: 2, sm: 4 },
                                alignItems: "start",
                            }}
                        >
                            <Box data-tour="query-overview">
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
                                    {SEARCH_TIPS.map((tip) =>
                                        createSearchTip(
                                            tip.query,
                                            tip.translationKey,
                                        ),
                                    )}
                                </Box>
                                <Box
                                    sx={{
                                        display: "flex",
                                        alignItems: "baseline",
                                        gap: 1,
                                        mt: 2,
                                        mb: 0.5,
                                    }}
                                >
                                    <Typography
                                        variant="overline"
                                        color="text.secondary"
                                    >
                                        {t("emptySearch.sort.title")}
                                    </Typography>
                                    <Typography
                                        variant="caption"
                                        color="text.disabled"
                                        sx={{ fontStyle: "italic" }}
                                    >
                                        {t("emptySearch.sort.hint")}
                                    </Typography>
                                </Box>
                                <Box
                                    component="ul"
                                    sx={{ m: 0, pl: 2.5, fontSize: "0.85rem" }}
                                >
                                    <li>
                                        <Box
                                            component="span"
                                            sx={sortChipSx}
                                            onClick={() =>
                                                performSearch(
                                                    "*",
                                                    "short_name",
                                                    "asc",
                                                )
                                            }
                                        >
                                            short_name
                                        </Box>{" "}
                                        - {t("emptySearch.sort.name")}
                                    </li>
                                    <li>
                                        <Box
                                            component="span"
                                            sx={sortChipSx}
                                            onClick={() =>
                                                performSearch(
                                                    "*",
                                                    "uploaded_datetime",
                                                    "desc",
                                                )
                                            }
                                        >
                                            uploaded_datetime
                                        </Box>{" "}
                                        - {t("emptySearch.sort.uploaded")}
                                    </li>
                                    <li>
                                        <Box
                                            component="span"
                                            sx={sortChipSx}
                                            onClick={() =>
                                                performSearch(
                                                    "*",
                                                    "tika_meta.dcterms_created",
                                                    "desc",
                                                )
                                            }
                                        >
                                            tika_meta.dcterms_created
                                        </Box>{" "}
                                        - {t("emptySearch.sort.created")}
                                    </li>
                                </Box>
                                <Typography
                                    variant="body2"
                                    sx={{
                                        display: "inline-block",
                                        mt: 1,
                                        cursor: "pointer",
                                        color: "primary.main",
                                        textDecoration: "underline",
                                        "&:hover": { color: "primary.dark" },
                                    }}
                                    onClick={() => {
                                        window.location.assign(
                                            "https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html#query-string-syntax",
                                        );
                                    }}
                                >
                                    {t("emptySearch.advancedGuide")}
                                </Typography>
                            </Box>
                            <Box data-tour="keyboard-shortcuts">
                                <Typography
                                    variant="overline"
                                    color="text.secondary"
                                    sx={{ display: "block", mb: 0.5 }}
                                >
                                    {t("emptySearch.hotkeys.title")}
                                </Typography>
                                <Table
                                    size="small"
                                    sx={{
                                        "& td": {
                                            fontSize: "0.82rem",
                                            border: 0,
                                            px: 0,
                                            py: 0.25,
                                        },
                                    }}
                                >
                                    <TableBody>
                                        {shortcutRegistry
                                            .filter(
                                                (action) =>
                                                    action.defaultKeys.length >
                                                        0 &&
                                                    action.id !== "results" &&
                                                    action.id !== "open" &&
                                                    action.id !==
                                                        "openBackground" &&
                                                    action.id !==
                                                        "shiftClickNegate" &&
                                                    action.id !==
                                                        "ctrlClickAccumulate",
                                            )
                                            .map((action) => (
                                                <TableRow key={action.id}>
                                                    <TableCell
                                                        sx={{
                                                            pr: 1.5,
                                                            verticalAlign:
                                                                "top",
                                                            py: "0.25rem !important",
                                                        }}
                                                    >
                                                        <KeyRecorder
                                                            actionId={action.id}
                                                            currentKeys={
                                                                resolvedBindings[
                                                                    action.id
                                                                ] ||
                                                                action.defaultKeys
                                                            }
                                                            defaultKeys={
                                                                action.defaultKeys
                                                            }
                                                            readOnly
                                                        />
                                                    </TableCell>
                                                    <TableCell
                                                        sx={{
                                                            verticalAlign:
                                                                "middle",
                                                            pt: "6px",
                                                        }}
                                                    >
                                                        <Box
                                                            sx={{
                                                                display: "flex",
                                                                alignItems:
                                                                    "center",
                                                                gap: 0.5,
                                                            }}
                                                        >
                                                            {action.icon && (
                                                                <Box
                                                                    component="span"
                                                                    sx={{
                                                                        display:
                                                                            "flex",
                                                                        color: "text.secondary",
                                                                        fontSize:
                                                                            "1rem",
                                                                    }}
                                                                >
                                                                    {
                                                                        action.icon
                                                                    }
                                                                </Box>
                                                            )}
                                                            <span>
                                                                {typeof action.labelKey ===
                                                                "string"
                                                                    ? t(
                                                                          action.labelKey,
                                                                      )
                                                                    : action.labelKey}
                                                            </span>
                                                        </Box>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                    </TableBody>
                                </Table>
                            </Box>
                        </Box>
                    </Box>
                </CardContent>
            </Card>
        </Box>
    );
};
