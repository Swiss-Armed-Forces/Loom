import {
    AttachFile,
    SubdirectoryArrowLeft,
    Download,
    Flag,
    LabelOutlined,
    ManageSearch,
    MarkEmailReadOutlined,
    Share,
    SummarizeOutlined,
    Translate,
    YoutubeSearchedForOutlined,
} from "@mui/icons-material";
import {
    Alert,
    AlertTitle,
    Box,
    Card,
    CardContent,
    CardHeader,
    Divider,
    Table,
    TableBody,
    TableCell,
    TableRow,
    Typography,
} from "@mui/material";
import { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    updateQuery,
    selectQuery,
    selectQueryError,
} from "@app/slices/searchSlice";

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

type HotkeyRow =
    | { type: "row"; keys: string[]; label: ReactNode; icon?: ReactNode }
    | { type: "divider" };

export const EmptySearchResults = () => {
    const searchQuery = useAppSelector(selectQuery);
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const HOTKEY_ROWS: HotkeyRow[] = [
        {
            type: "row",
            keys: ["↓", "j"],
            label: t("emptySearch.hotkeys.moveDown"),
        },
        {
            type: "row",
            keys: ["↑", "k"],
            label: t("emptySearch.hotkeys.moveUp"),
        },
        {
            type: "row",
            keys: ["←", "h"],
            label: t("emptySearch.hotkeys.prevCenterTab"),
        },
        {
            type: "row",
            keys: ["→", "l"],
            label: t("emptySearch.hotkeys.nextCenterTab"),
        },
        {
            type: "row",
            keys: ["Shift + ←", "Shift + h"],
            label: t("emptySearch.hotkeys.prevTab"),
        },
        {
            type: "row",
            keys: ["Shift + →", "Shift + l"],
            label: t("emptySearch.hotkeys.nextTab"),
        },
        {
            type: "row",
            keys: ["Enter", "i", "Double-click"],
            label: t("emptySearch.hotkeys.openOrClose"),
        },
        {
            type: "row",
            keys: ["Shift + Enter", "Shift + i", "Ctrl + click"],
            label: t("emptySearch.hotkeys.openBackground"),
        },
        {
            type: "row",
            keys: ["Shift + click"],
            label: (
                <>
                    {t("emptySearch.hotkeys.shiftClickNegate")}{" "}
                    <Box
                        component="span"
                        sx={{
                            opacity: 0.5,
                            fontSize: "0.9em",
                            whiteSpace: "nowrap",
                        }}
                    >
                        (
                        <ManageSearch
                            fontSize="inherit"
                            sx={{ verticalAlign: "middle" }}
                        />{" "}
                        icon)
                    </Box>
                </>
            ),
        },
        {
            type: "row",
            keys: ["Escape"],
            label: t("emptySearch.hotkeys.escapeAction"),
        },
        {
            type: "row",
            keys: ["/"],
            label: t("emptySearch.hotkeys.focusSearch"),
        },
        { type: "divider" },
        {
            type: "row",
            keys: ["f"],
            icon: <Flag fontSize="inherit" />,
            label: (
                <>
                    <strong>F</strong>lag / unflag
                </>
            ),
        },
        {
            type: "row",
            keys: ["s"],
            icon: <MarkEmailReadOutlined fontSize="inherit" />,
            label: (
                <>
                    <strong>S</strong>een / unseen
                </>
            ),
        },
        {
            type: "row",
            keys: ["t"],
            icon: <LabelOutlined fontSize="inherit" />,
            label: (
                <>
                    <strong>T</strong>ag
                </>
            ),
        },
        {
            type: "row",
            keys: ["n"],
            icon: (
                <SubdirectoryArrowLeft
                    fontSize="inherit"
                    sx={{ transform: "rotate(90deg)" }}
                />
            ),
            label: (
                <>
                    <strong>N</strong>avigate to parent file
                </>
            ),
        },
        {
            type: "row",
            keys: ["Shift + n"],
            icon: <AttachFile fontSize="inherit" />,
            label: (
                <>
                    <strong>N</strong>avigate to child file
                </>
            ),
        },
        {
            type: "row",
            keys: ["Shift + c"],
            icon: <Share fontSize="inherit" />,
            label: (
                <>
                    <strong>C</strong>opy share link
                </>
            ),
        },
        {
            type: "row",
            keys: ["Shift + t"],
            icon: <Translate fontSize="inherit" />,
            label: (
                <>
                    <strong>T</strong>ranslate
                </>
            ),
        },
        {
            type: "row",
            keys: ["Shift + s"],
            icon: <SummarizeOutlined fontSize="inherit" />,
            label: (
                <>
                    <strong>S</strong>ummarize
                </>
            ),
        },
        {
            type: "row",
            keys: ["r"],
            icon: <YoutubeSearchedForOutlined fontSize="inherit" />,
            label: (
                <>
                    <strong>R</strong>e-index
                </>
            ),
        },
        {
            type: "row",
            keys: ["d"],
            icon: <Download fontSize="inherit" />,
            label: (
                <>
                    <strong>D</strong>ownload
                </>
            ),
        },
    ];
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
        <li key={query}>
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
                            <Box>
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
                                        {HOTKEY_ROWS.map((row, i) => {
                                            if (row.type === "divider") {
                                                return (
                                                    <TableRow
                                                        key={`divider-${i}`}
                                                    >
                                                        <TableCell
                                                            colSpan={2}
                                                            sx={{
                                                                py: "0.3rem !important",
                                                            }}
                                                        >
                                                            <Divider />
                                                        </TableCell>
                                                    </TableRow>
                                                );
                                            }
                                            return (
                                                <TableRow
                                                    key={row.keys.join("|")}
                                                >
                                                    <TableCell
                                                        sx={{
                                                            pr: 1.5,
                                                            verticalAlign:
                                                                "top",
                                                        }}
                                                    >
                                                        {row.keys.map(
                                                            (key, ki) => (
                                                                <span key={key}>
                                                                    <kbd>
                                                                        {key}
                                                                    </kbd>
                                                                    {ki <
                                                                        row.keys
                                                                            .length -
                                                                            1 &&
                                                                        " / "}
                                                                </span>
                                                            ),
                                                        )}
                                                    </TableCell>
                                                    <TableCell
                                                        sx={{
                                                            verticalAlign:
                                                                "top",
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
                                                            {row.icon && (
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
                                                                    {row.icon}
                                                                </Box>
                                                            )}
                                                            <span>
                                                                {row.label}
                                                            </span>
                                                        </Box>
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })}
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
