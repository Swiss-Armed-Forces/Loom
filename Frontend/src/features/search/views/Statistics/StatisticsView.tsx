import {
    BarChart,
    Description,
    VerticalAlignBottom,
    VerticalAlignTop,
} from "@mui/icons-material";
import {
    Divider,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    Typography,
} from "@mui/material";
import { SelectChangeEvent } from "@mui/material/Select";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";
import { toast } from "react-toastify";

import {
    getTermsStat,
    getHistogramStat,
    getTermsStats,
    getHistogramStats,
} from "@app/api";
import { useAppSelector } from "@app/hooks";
import {
    selectQuery,
    selectStatsData,
    selectDisplayStat,
    selectDisplayHistogramStat,
    selectTermsStats,
    selectHistogramStats,
    selectHistogramData,
    updateQuery,
    clearStats,
    fillTermsData,
    fillHistogramData,
    fillTermsStats,
    fillHistogramStats,
    setDisplayStat,
    setDisplayHistogramStat,
} from "@app/slices/searchSlice";
import { AppDispatch } from "@app/store";
import {
    formatFileSize,
    updateFieldOfQuery,
} from "@features/common/utils/helpers";
import {
    Chart,
    HistogramChart,
    computeOthersCount,
} from "@features/search/components";

import styles from "./StatisticsView.module.css";
import {
    DATE_STAT_ORDER,
    NUMBER_STAT_ORDER,
    TERMS_STAT_ORDER,
} from "./statOrder";

const CHART_HEIGHT = 230;
const AUTO_REFRESH_MS = 60_000;
const PIE_AMOUNT = 5;

/** Strip Dublin Core / Tika namespace prefixes that add noise for end users. */
const cleanStatLabel = (label: string): string =>
    label.replace(/^(Dcterms|Dc|Tika)\s+/i, "");

const sortStats = <T extends { id: string; label: string }>(
    stats: T[],
    order: string[],
): T[] =>
    [...stats].sort((a, b) => {
        const ai = order.indexOf(a.id);
        const bi = order.indexOf(b.id);
        if (ai === -1 && bi === -1) return a.label.localeCompare(b.label);
        if (ai === -1) return 1;
        if (bi === -1) return -1;
        return ai - bi;
    });

const HISTOGRAM_STAT_ORDER = [...DATE_STAT_ORDER, ...NUMBER_STAT_ORDER];

const translationKey = (id: string) =>
    id.replace(/\.keyword$/, "").replace(/\./g, "_");

export const StatisticsView = () => {
    const searchQuery = useAppSelector(selectQuery);
    const stats = useAppSelector(selectStatsData);
    const histogramData = useAppSelector(selectHistogramData);
    const displayStat = useAppSelector(selectDisplayStat);
    const displayHistogramStat = useAppSelector(selectDisplayHistogramStat);
    const termsStats = useAppSelector(selectTermsStats);
    const histogramStats = useAppSelector(selectHistogramStats);
    const dispatch = useDispatch<AppDispatch>();
    const { t } = useTranslation();
    const [highlightedGroup, setHighlightedGroup] = useState<string | null>(
        null,
    );
    const abortControllerRef = useRef<AbortController | null>(null);

    // Group names in pie-chart color-index order (ascending by count), used to
    // colour the bar chart consistently with the pie chart.
    const groupColorOrder = useMemo((): string[] => {
        if (!stats?.termsData?.data) return [];
        return [...stats.termsData.data]
            .sort((a, b) => a.hitsCount - b.hitsCount)
            .map((e) => e.name);
    }, [stats?.termsData?.data]);

    // When the pie has an "others" slice at index 0, named slices start at
    // CHART_COLORS[1]. The histogram must apply the same offset.
    const groupColorOffset = useMemo((): number => {
        if (!stats?.termsData?.data) return 0;
        return computeOthersCount(
            stats.termsData.data,
            stats.termsData.fileCount,
        ) > 0
            ? 1
            : 0;
    }, [stats?.termsData?.data, stats?.termsData?.fileCount]);

    const sortedTermsStats = sortStats(termsStats, TERMS_STAT_ORDER);
    const sortedHistogramStats = sortStats(
        histogramStats,
        HISTOGRAM_STAT_ORDER,
    );

    const isNumberHistogram = histogramData?.histogramType === "number";

    // Fetch available stats once on mount — they don't change with the query.
    // Skip when already populated from the localStorage cache.
    useEffect(() => {
        if (termsStats.length > 0 && histogramStats.length > 0) return;
        Promise.all([getTermsStats(), getHistogramStats()])
            .then(([terms, histograms]) => {
                dispatch(fillTermsStats(terms));
                dispatch(fillHistogramStats(histograms));
            })
            .catch((err) => {
                toast.error(
                    "Cannot load available stats. Error: " +
                        (err["detail"] ? err["detail"] : err),
                );
            });
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const fetchStats = useCallback(() => {
        if (!searchQuery?.query?.trim()) {
            dispatch(clearStats());
            return;
        }
        // Abort any previous in-flight fetch so stale responses don't overwrite
        // results from a newer fetch that completes first.
        abortControllerRef.current?.abort();
        const controller = new AbortController();
        abortControllerRef.current = controller;

        if (controller.signal.aborted) return;
        const statsQuery = { ...searchQuery, id: null };
        getTermsStat(statsQuery, displayStat, PIE_AMOUNT)
            .then((result) => {
                if (!controller.signal.aborted) dispatch(fillTermsData(result));
            })
            .catch((err) => {
                if (!controller.signal.aborted)
                    toast.error(
                        "Cannot load statistic results. Error: " +
                            (err["detail"] ? err["detail"] : err),
                    );
            });
        getHistogramStat(statsQuery, displayHistogramStat, displayStat)
            .then((result) => {
                if (!controller.signal.aborted)
                    dispatch(fillHistogramData(result));
            })
            .catch((err) => {
                if (!controller.signal.aborted)
                    toast.error(
                        "Cannot load grouped statistic results. Error: " +
                            (err["detail"] ? err["detail"] : err),
                    );
            });
    }, [searchQuery, displayStat, displayHistogramStat, dispatch]);

    // Skip the stats fetch on the initial mount so that an F5 with an
    // unchanged query (state restored from localStorage) does not trigger any
    // backend calls. The effect re-runs whenever fetchStats changes — i.e.
    // when the query, displayStat, or displayHistogramStat actually changes.
    const statsMountedRef = useRef(false);
    useEffect(() => {
        if (!statsMountedRef.current) {
            statsMountedRef.current = true;
            return;
        }
        fetchStats();
    }, [fetchStats]);

    useEffect(() => {
        const interval = setInterval(fetchStats, AUTO_REFRESH_MS);
        return () => clearInterval(interval);
    }, [fetchStats]);

    const handleStatChange = (event: SelectChangeEvent) => {
        dispatch(setDisplayStat(event.target.value));
    };

    const handleHistogramStatChange = (event: SelectChangeEvent) => {
        dispatch(setDisplayHistogramStat(event.target.value));
    };

    const handleUpdateQuery = (
        queryKeyword: string,
        searchTerm: string | string[],
        negate?: boolean,
        noQuote?: boolean,
    ) => {
        const newQuery = updateFieldOfQuery(
            searchQuery?.query ?? "",
            queryKeyword,
            searchTerm,
            noQuote ?? false,
            negate,
        );
        dispatch(updateQuery({ query: newQuery }));
    };

    const handleUpdateRangeQuery = (
        fieldName: string,
        startVal: string,
        endVal: string,
    ) => {
        const range =
            endVal === "*"
                ? `[${startVal} TO *]`
                : `[${startVal} TO ${endVal}}`;
        const newQuery = updateFieldOfQuery(
            searchQuery?.query ?? "",
            fieldName,
            range,
            true,
        );
        dispatch(updateQuery({ query: newQuery }));
    };

    const formatHistogramValue = (val: number | undefined): string => {
        if (val === undefined) return "—";
        if (displayHistogramStat === "size") return formatFileSize(val);
        if (isNumberHistogram) return val.toLocaleString();
        return new Date(val).toLocaleDateString(undefined, {
            day: "numeric",
            month: "short",
            year: "numeric",
        });
    };

    return (
        <div className={styles.statisticsContainer}>
            <section className={styles.chartSection}>
                <FormControl
                    size="small"
                    fullWidth
                    className={styles.statSelector}
                >
                    <InputLabel id="stat-select-label">Stat</InputLabel>
                    <Select
                        labelId="stat-select-label"
                        id="stat-select"
                        value={displayStat}
                        label="Stat"
                        onChange={handleStatChange}
                    >
                        {sortedTermsStats.map((stat) => (
                            <MenuItem
                                key={`key-${stat.id}`}
                                value={stat.id}
                                selected={stat.id === displayStat}
                            >
                                {cleanStatLabel(
                                    t(
                                        `statisticsView.${translationKey(stat.id)}Title`,
                                        {
                                            defaultValue: stat.label,
                                        },
                                    ),
                                )}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
                <Chart
                    entries={stats.termsData?.data ?? []}
                    fileCount={stats.termsData?.fileCount ?? 0}
                    handleUpdateQuery={handleUpdateQuery}
                    queryKeyword={stats.termsData?.key ?? ""}
                    height={CHART_HEIGHT}
                    onGroupHighlight={setHighlightedGroup}
                    highlightedGroup={highlightedGroup}
                />
            </section>

            <Divider />

            <section className={styles.chartSection}>
                <FormControl
                    size="small"
                    fullWidth
                    className={styles.statSelector}
                >
                    <InputLabel id="histogram-stat-select-label">
                        Histogram stat
                    </InputLabel>
                    <Select
                        labelId="histogram-stat-select-label"
                        id="histogram-stat-select"
                        value={displayHistogramStat}
                        label="Histogram stat"
                        onChange={handleHistogramStatChange}
                    >
                        {sortedHistogramStats.map((stat) => (
                            <MenuItem
                                key={`key-${stat.id}`}
                                value={stat.id}
                                selected={stat.id === displayHistogramStat}
                            >
                                {cleanStatLabel(
                                    t(
                                        `statisticsView.${translationKey(stat.id)}Title`,
                                        {
                                            defaultValue: stat.label,
                                        },
                                    ),
                                )}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
                <HistogramChart
                    groupedEntries={histogramData?.data ?? null}
                    height={CHART_HEIGHT}
                    groupColorOrder={groupColorOrder}
                    colorOffset={groupColorOffset}
                    highlightedGroup={highlightedGroup}
                    onGroupHighlight={setHighlightedGroup}
                    chartType={isNumberHistogram ? "number" : "date"}
                    onRangeSelect={(start, end) =>
                        handleUpdateRangeQuery(
                            histogramData?.key ?? "",
                            start,
                            end,
                        )
                    }
                    onGroupFilter={(group, negate, noQuote) =>
                        handleUpdateQuery(
                            stats.termsData?.key ?? "",
                            group,
                            negate,
                            noQuote,
                        )
                    }
                />
            </section>

            <Divider />

            <section className={styles.summarySection}>
                <Typography variant="overline" className={styles.sectionLabel}>
                    {t("statisticsView.summaryTitle")}
                </Typography>
                <div className={styles.summaryGrid}>
                    <div className={styles.summaryItem}>
                        <Description
                            fontSize="small"
                            className={styles.summaryIcon}
                        />
                        <div>
                            <Typography
                                variant="caption"
                                color="text.secondary"
                            >
                                {t("statisticsView.totalDocuments")}
                            </Typography>
                            <Typography
                                variant="body2"
                                sx={{ fontWeight: "medium" }}
                            >
                                {stats.termsData?.fileCount ?? "—"}
                            </Typography>
                        </div>
                    </div>
                    <div className={styles.summaryItem}>
                        <BarChart
                            fontSize="small"
                            className={styles.summaryIcon}
                        />
                        <div>
                            <Typography
                                variant="caption"
                                color="text.secondary"
                            >
                                {t("statisticsView.histogramDocuments")}
                            </Typography>
                            <Typography
                                variant="body2"
                                sx={{ fontWeight: "medium" }}
                            >
                                {histogramData?.fileCount ?? "—"}
                            </Typography>
                        </div>
                    </div>
                    <div className={styles.summaryItem}>
                        <VerticalAlignBottom
                            fontSize="small"
                            className={styles.summaryIcon}
                        />
                        <div>
                            <Typography
                                variant="caption"
                                color="text.secondary"
                            >
                                {t("statisticsView.histogramMin")}
                            </Typography>
                            <Typography
                                variant="body2"
                                sx={{ fontWeight: "medium" }}
                            >
                                {formatHistogramValue(histogramData?.minValue)}
                            </Typography>
                        </div>
                    </div>
                    <div className={styles.summaryItem}>
                        <VerticalAlignTop
                            fontSize="small"
                            className={styles.summaryIcon}
                        />
                        <div>
                            <Typography
                                variant="caption"
                                color="text.secondary"
                            >
                                {t("statisticsView.histogramMax")}
                            </Typography>
                            <Typography
                                variant="body2"
                                sx={{ fontWeight: "medium" }}
                            >
                                {formatHistogramValue(histogramData?.maxValue)}
                            </Typography>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
};
