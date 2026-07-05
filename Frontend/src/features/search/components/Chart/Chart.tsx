import {
    DefaultizedPieValueType,
    PieItemIdentifier,
    PieValueType,
} from "@mui/x-charts/models";
import { PieChart } from "@mui/x-charts/PieChart";
import { Fragment, useState } from "react";

import { HitsPerGroupEntryModel } from "@app/api";

import styles from "./Chart.module.css";

interface ChartProps {
    entries: HitsPerGroupEntryModel[];
    handleUpdateQuery: (key: string, value: string | string[]) => void;
    queryKeyword: string;
    compact: number;
    height?: number;
}

// onHighlightChange provides dataIndex as optional — use a wider type for state
type PieHighlightItem = {
    type: "pie";
    seriesId: string;
    dataIndex?: number;
} | null;

const PIE_SERIES_ID = "pie";

const MISC_ID = "misc_id";

const COLORS = [
    "#0088FE",
    "#00C49F",
    "#FFBB28",
    "#FF8042",
    "#d32f2f",
    "#7b1fa2",
    "#5d4037",
    "#455a64",
];

const arcLabel = (
    item: Omit<DefaultizedPieValueType, "label"> & { label?: string },
): string => {
    return `${item.value}`;
};

const processEntries = (entries: HitsPerGroupEntryModel[]) => {
    return entries
        .map((e) => ({
            id: `${e.name}_id`,
            value: e.hitsCount,
            label: e.name,
        }))
        .sort((a, b) => (a.value < b.value ? -1 : a.value === b.value ? 0 : 1));
};

const summarizeEntries = (entries: PieValueType[], max: number) => {
    if (entries.length <= max) return { data: entries, others: [] };
    const result: PieValueType[] = [];
    const others: PieValueType[] = [];
    entries.toReversed().forEach((e) => {
        if (result.length < max - 1) result.push(e);
        else others.push(e);
    });
    result.unshift({
        id: MISC_ID,
        value: others.reduce((sum, e) => sum + (e.value as number), 0),
        label: "others",
    } satisfies PieValueType);
    return { data: result.reverse(), others };
};

export const Chart = ({
    entries,
    handleUpdateQuery,
    queryKeyword,
    compact,
    height = 500,
}: ChartProps) => {
    const dataAll = processEntries(entries);
    const { data, others } = summarizeEntries(dataAll, compact);

    const [highlightedItem, setHighlightedItem] =
        useState<PieHighlightItem>(null);

    const handleClick = (
        _: any,
        __: PieItemIdentifier,
        item: DefaultizedPieValueType,
    ) => {
        let term: string | string[];
        if (item.id === MISC_ID) {
            term = others.map((other) => `${other.label}`);
        } else {
            term = item.label ? `${item.label}` : "";
        }
        handleUpdateQuery(queryKeyword, term);
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
                        onHighlightChange={setHighlightedItem}
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
                                    onMouseEnter={() =>
                                        setHighlightedItem({
                                            type: "pie",
                                            seriesId: PIE_SERIES_ID,
                                            dataIndex: i,
                                        })
                                    }
                                    onMouseLeave={() =>
                                        setHighlightedItem(null)
                                    }
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
