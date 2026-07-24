import {
    DefaultizedPieValueType,
    PieItemIdentifier,
    PieValueType,
} from "@mui/x-charts/models";
import { PieChart } from "@mui/x-charts/PieChart";
import React, { Fragment, useEffect, useState } from "react";

import { HitsPerGroupEntryModel } from "@app/api";

import {
    CHART_COLORS,
    NONE_LABEL,
    OTHERS_LABEL,
    computeOthersCount,
} from "../chartColors";

import styles from "./Chart.module.css";

interface ChartProps {
    entries: HitsPerGroupEntryModel[];
    fileCount: number;
    othersCount?: number;
    handleUpdateQuery: (
        key: string,
        value: string | string[],
        negate?: boolean,
        noQuote?: boolean,
    ) => void;
    queryKeyword: string;
    height?: number;
    onGroupHighlight?: (group: string | null) => void;
    highlightedGroup?: string | null;
}

// onHighlightChange provides dataIndex as optional — use a wider type for state
type PieHighlightItem = {
    type: "pie";
    seriesId: string;
    dataIndex?: number;
} | null;

const PIE_SERIES_ID = "pie";

const MISC_ID = "misc_id";

const COLORS = CHART_COLORS;

const arcLabel = (
    item: Omit<DefaultizedPieValueType, "label"> & { label?: string },
): string => {
    return `${item.value}`;
};

const buildPieData = (
    entries: HitsPerGroupEntryModel[],
    fileCount: number,
    othersCount?: number,
): PieValueType[] => {
    const named: PieValueType[] = entries
        .map((e) => ({
            id: `${e.name}_id`,
            value: e.hitsCount,
            label: e.name,
        }))
        .sort((a, b) => a.value - b.value);

    const resolvedOthersCount =
        othersCount ?? computeOthersCount(entries, fileCount);

    if (resolvedOthersCount > 0) {
        return [
            {
                id: MISC_ID,
                value: resolvedOthersCount,
                label: OTHERS_LABEL,
            } satisfies PieValueType,
            ...named,
        ];
    }
    return named;
};

export const Chart = ({
    entries,
    fileCount,
    othersCount,
    handleUpdateQuery,
    queryKeyword,
    height = 500,
    onGroupHighlight,
    highlightedGroup,
}: ChartProps) => {
    const data = buildPieData(entries, fileCount, othersCount);

    const [highlightedItem, setHighlightedItem] =
        useState<PieHighlightItem>(null);

    // Sync external highlight (from histogram hover) into the pie chart.
    useEffect(() => {
        if (highlightedGroup === null || highlightedGroup === undefined) {
            setHighlightedItem(null);
            return;
        }
        const idx = data.findIndex((d) => d.label === highlightedGroup);
        setHighlightedItem(
            idx >= 0
                ? { type: "pie", seriesId: PIE_SERIES_ID, dataIndex: idx }
                : null,
        );
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [highlightedGroup]);

    const handleHighlightChange = (item: PieHighlightItem) => {
        setHighlightedItem(item);
        if (item === null || item.dataIndex === undefined) {
            onGroupHighlight?.(null);
        } else {
            onGroupHighlight?.((data[item.dataIndex]?.label as string) ?? null);
        }
    };

    const handleClick = (
        event: React.MouseEvent<SVGPathElement, MouseEvent>,
        __: PieItemIdentifier,
        item: DefaultizedPieValueType,
    ) => {
        const negate = event.shiftKey;
        if (item.id === MISC_ID) {
            // Negate: exclude all shown named items so only "others" remain
            const shownLabels = data
                .filter((d) => d.id !== MISC_ID)
                .map((d) => `${d.label}`);
            handleUpdateQuery(queryKeyword, shownLabels, !negate);
        } else if (item.label === NONE_LABEL) {
            // "(none)" = field absent. Normal click → NOT field:* (no field set),
            // shift-click → field:* (field exists), i.e. the inverse.
            handleUpdateQuery(queryKeyword, "*", !negate, true);
        } else {
            handleUpdateQuery(
                queryKeyword,
                item.label ? `${item.label}` : "",
                negate,
            );
        }
    };

    const anyHighlighted = highlightedItem !== null;

    return (
        <Fragment>
            {entries && (
                <>
                    <PieChart
                        height={height}
                        hideLegend
                        onItemClick={handleClick}
                        colors={COLORS}
                        highlightedItem={highlightedItem}
                        onHighlightChange={handleHighlightChange}
                        series={[
                            {
                                id: PIE_SERIES_ID,
                                data,
                                arcLabel,
                                arcLabelMinAngle: 45,
                                highlightScope: {
                                    fade: "global",
                                    highlight: "item",
                                },
                                faded: {
                                    innerRadius: 30,
                                    additionalRadius: -30,
                                    color: "gray",
                                },
                            },
                        ]}
                    />
                    <ul className={styles.legend}>
                        {data.map((item, i) => {
                            const isHighlighted =
                                anyHighlighted &&
                                highlightedItem?.dataIndex === i;
                            const isFaded = anyHighlighted && !isHighlighted;
                            return (
                                <li
                                    key={item.id as string}
                                    className={`${styles.legendItem} ${isFaded ? styles.faded : ""} ${isHighlighted ? styles.highlighted : ""}`}
                                    onMouseEnter={() => {
                                        setHighlightedItem({
                                            type: "pie",
                                            seriesId: PIE_SERIES_ID,
                                            dataIndex: i,
                                        });
                                        onGroupHighlight?.(
                                            item.label as string,
                                        );
                                    }}
                                    onMouseLeave={() => {
                                        setHighlightedItem(null);
                                        onGroupHighlight?.(null);
                                    }}
                                >
                                    <span
                                        className={styles.legendSwatch}
                                        style={{
                                            background:
                                                COLORS[i % COLORS.length],
                                        }}
                                    />
                                    <span className={styles.legendLabel}>
                                        {item.label as string}
                                    </span>
                                </li>
                            );
                        })}
                    </ul>
                </>
            )}
        </Fragment>
    );
};
