import { Equalizer, Numbers, StackedLineChart } from "@mui/icons-material";
import {
    Divider,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    Skeleton,
    Typography,
} from "@mui/material";
import { SelectChangeEvent } from "@mui/material/Select";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";
import { toast } from "react-toastify";

import { getStatSummary, getStatGeneric, Stat } from "@app/api";
import { useAppSelector } from "@app/hooks";
import {
    selectIsLoading,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import {
    selectQuery,
    selectStatsData,
    selectDisplayStat,
    updateQuery,
    fillStatsSummary,
    fillStatsGeneric,
    fillStatsTags,
    setDisplayStat,
} from "@app/slices/searchSlice";
import { AppDispatch } from "@app/store";
import {
    formatFileSize,
    updateFieldOfQuery,
} from "@features/common/utils/helpers";
import { TagsList } from "@features/search/components";
import { Chart } from "@features/search/components";

import styles from "./StatisticsView.module.css";

const PIE_AMOUNT = 5;
const CHART_HEIGHT = 280;
const STAT_VALUES = Object.values(Stat);

export const StatisticsView = () => {
    const searchQuery = useAppSelector(selectQuery);
    const stats = useAppSelector(selectStatsData);
    const isLoading = useAppSelector(selectIsLoading);
    const displayStat = useAppSelector(selectDisplayStat);
    const dispatch = useDispatch<AppDispatch>();
    const { t } = useTranslation();

    useEffect(() => {
        if (!searchQuery) return;
        dispatch(startLoadingIndicator());
        getStatGeneric(searchQuery, Stat.Tags)
            .then((result) => {
                dispatch(fillStatsTags(result));
            })
            .catch((err) => {
                toast.error(
                    "Cannot load GENERIC statistic results. Error: " +
                        (err["detail"] ? err["detail"] : err),
                );
                dispatch(fillStatsGeneric(null));
            });
        getStatSummary(searchQuery)
            .then((result) => {
                dispatch(fillStatsSummary(result));
            })
            .catch((err) => {
                toast.error(
                    "Cannot load statistic results. Error: " +
                        (err["detail"] ? err["detail"] : err),
                );
                dispatch(fillStatsSummary(null));
            })
            .finally(() => {
                dispatch(stopLoadingIndicator());
            });
    }, [searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (!searchQuery) return;
        getStatGeneric(searchQuery, displayStat)
            .then((result) => {
                dispatch(fillStatsGeneric(result));
            })
            .catch((err) => {
                toast.error(
                    "Cannot load GENERIC statistic results. Error: " +
                        (err["detail"] ? err["detail"] : err),
                );
                dispatch(fillStatsGeneric(null));
            });
    }, [searchQuery, displayStat]); // eslint-disable-line react-hooks/exhaustive-deps

    const handleUpdateQuery = (
        queryKeyword: string,
        searchTerm: string | string[],
    ) => {
        const newQuery = updateFieldOfQuery(
            searchQuery?.query ?? "",
            queryKeyword,
            searchTerm,
        );
        dispatch(
            updateQuery({
                query: newQuery,
            }),
        );
    };

    const handleStatChange = (event: SelectChangeEvent) => {
        dispatch(setDisplayStat(event.target.value as Stat));
    };

    if (isLoading) {
        return (
            <div className={styles.skeletonLoadingContainer}>
                <Skeleton variant="text" />
                <Skeleton variant="text" />
                <Skeleton variant="text" />
                <Skeleton variant="text" />
            </div>
        );
    }

    if (!isLoading && (!stats?.summary?.count || stats?.summary?.count === 0)) {
        return null;
    }

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
                        {STAT_VALUES.map((value) => (
                            <MenuItem
                                key={`key-${value}`}
                                value={value}
                                disabled={value === "tags"}
                                selected={value === displayStat}
                            >
                                {t(`statisticsView.${value}Title`)}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
                {!!stats?.generic && (
                    <Chart
                        entries={stats?.generic?.data}
                        handleUpdateQuery={handleUpdateQuery}
                        queryKeyword={stats.generic?.key}
                        compact={PIE_AMOUNT}
                        height={CHART_HEIGHT}
                    />
                )}
            </section>

            <Divider />

            <section className={styles.summarySection}>
                <Typography variant="overline" className={styles.sectionLabel}>
                    {t("statisticsView.summaryTitle")}
                </Typography>
                <div className={styles.summaryGrid}>
                    <div className={styles.summaryItem}>
                        <Numbers
                            fontSize="small"
                            className={styles.summaryIcon}
                        />
                        <div>
                            <Typography
                                variant="caption"
                                color="text.secondary"
                            >
                                {t("statisticsView.numberOfFiles")}
                            </Typography>
                            <Typography
                                variant="body2"
                                sx={{ fontWeight: "medium" }}
                            >
                                {stats?.summary?.count}
                            </Typography>
                        </div>
                    </div>
                    <div className={styles.summaryItem}>
                        <Equalizer
                            fontSize="small"
                            className={styles.summaryIcon}
                        />
                        <div>
                            <Typography
                                variant="caption"
                                color="text.secondary"
                            >
                                {t("statisticsView.minFileSize")}
                            </Typography>
                            <Typography
                                variant="body2"
                                sx={{ fontWeight: "medium" }}
                            >
                                {formatFileSize(stats?.summary?.min ?? 0)}
                            </Typography>
                        </div>
                    </div>
                    <div className={styles.summaryItem}>
                        <StackedLineChart
                            fontSize="small"
                            className={styles.summaryIcon}
                        />
                        <div>
                            <Typography
                                variant="caption"
                                color="text.secondary"
                            >
                                {t("statisticsView.avgFileSize")}
                            </Typography>
                            <Typography
                                variant="body2"
                                sx={{ fontWeight: "medium" }}
                            >
                                {formatFileSize(stats?.summary?.avg ?? 0)}
                            </Typography>
                        </div>
                    </div>
                    <div className={styles.summaryItem}>
                        <Equalizer
                            fontSize="small"
                            className={styles.summaryIcon}
                        />
                        <div>
                            <Typography
                                variant="caption"
                                color="text.secondary"
                            >
                                {t("statisticsView.maxFileSize")}
                            </Typography>
                            <Typography
                                variant="body2"
                                sx={{ fontWeight: "medium" }}
                            >
                                {formatFileSize(stats?.summary?.max ?? 0)}
                            </Typography>
                        </div>
                    </div>
                </div>
                {!!stats?.tags?.data && (
                    <div className={styles.tagsContainer}>
                        <TagsList
                            tags={stats.tags.data.map((e) => e.name)}
                            tagStats={stats.tags}
                        />
                    </div>
                )}
            </section>
        </div>
    );
};
