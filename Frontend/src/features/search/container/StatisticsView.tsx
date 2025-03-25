import { useEffect } from "react";
import { useAppSelector } from "../../../app/hooks";
import {
    selectQuery,
    selectStatsData,
    selectDisplayStat,
    updateQuery,
    fillStatsSummary,
    fillStatsGeneric,
    fillStatsTags,
    setDisplayStat,
} from "../searchSlice";
import { useDispatch } from "react-redux";
import {
    selectIsLoading,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "../../common/commonSlice";
import {
    Avatar,
    Grid,
    List,
    ListItem,
    ListItemAvatar,
    ListItemText,
    Skeleton,
    Typography,
} from "@mui/material";
import styles from "./StatisticsView.module.css";
import { Equalizer, Numbers, StackedLineChart } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { formatFileSize } from "../util";
import { replaceSectionIfExists } from "../SearchQueryUtils";
import { toast } from "react-toastify";
import { Chart } from "./Chart";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import Select, { SelectChangeEvent } from "@mui/material/Select";
import { AppDispatch } from "../../../app/store.ts";
import { getStatSummary, getStatGeneric, Stat } from "../../../app/api";
import { TagsList } from "../../common/components/tags/TagsList.tsx";
import { EmptySearchResults } from "../components/EmptySearchResults.tsx";

const PIE_AMOUNT = 5;

export function StatisticsView() {
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

    const handleUpdateQuery = (queryKeyword: string, searchTerm: string) => {
        const newQuery = replaceSectionIfExists(
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
        return <EmptySearchResults />;
    }

    return (
        <Grid
            container
            spacing={2}
            className={styles.statisticsContainer}
            columns={12}
        >
            <Grid item xs={3}>
                <Typography variant="h4">
                    {t("statisticsView.summaryTitle")}
                </Typography>
                <List>
                    <ListItem>
                        <ListItemAvatar>
                            <Avatar>
                                <Numbers />
                            </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                            primary={t("statisticsView.numberOfFiles")}
                            secondary={stats?.summary?.count}
                        />
                    </ListItem>
                    <ListItem>
                        <ListItemAvatar>
                            <Avatar>
                                <Equalizer />
                            </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                            primary={t("statisticsView.minFileSize")}
                            secondary={formatFileSize(stats?.summary?.min ?? 0)}
                        />
                    </ListItem>
                    <ListItem>
                        <ListItemAvatar>
                            <Avatar>
                                <StackedLineChart />
                            </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                            primary={t("statisticsView.avgFileSize")}
                            secondary={formatFileSize(stats?.summary?.avg ?? 0)}
                        />
                    </ListItem>
                    <ListItem>
                        <ListItemAvatar>
                            <Avatar>
                                <Equalizer />
                            </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                            primary={t("statisticsView.maxFileSize")}
                            secondary={formatFileSize(stats?.summary?.max ?? 0)}
                        />
                    </ListItem>
                    <br />
                    {!!stats?.tags?.data && (
                        <TagsList
                            tags={stats.tags.data.map((e) => e.name)}
                            tagStats={stats.tags}
                        />
                    )}
                </List>
            </Grid>
            {!!stats?.generic && (
                <Grid item xs={5}>
                    <Chart
                        entries={stats?.generic?.data}
                        title={t(`statisticsView.${stats.generic?.stat}Title`)}
                        handleUpdateQuery={handleUpdateQuery}
                        queryKeyword={stats.generic?.key}
                        compact={PIE_AMOUNT}
                    ></Chart>
                </Grid>
            )}
            <Grid item xs={2}>
                <FormControl fullWidth>
                    <InputLabel id="stat-select-label">Stat</InputLabel>
                    <Select
                        labelId="stat-select-label"
                        id="stat-select"
                        value={displayStat}
                        label="Stat"
                        onChange={handleStatChange}
                    >
                        {Object.values(Stat).map((value) => (
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
            </Grid>
        </Grid>
    );
}
