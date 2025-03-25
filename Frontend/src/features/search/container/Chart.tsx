import { PieChart } from "@mui/x-charts/PieChart";
import {
    DefaultizedPieValueType,
    PieItemIdentifier,
    PieValueType,
} from "@mui/x-charts/models";

import { Typography } from "@mui/material";

import { Fragment } from "react";
import { HitsPerGroupEntryModel } from "../../../app/api";

interface ChartProps {
    entries: HitsPerGroupEntryModel[];
    title: string;
    handleUpdateQuery: (key: string, value: string) => void;
    queryKeyword: string;
    compact: number;
}

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

function arcLabel(
    item: Omit<DefaultizedPieValueType, "label"> & {
        label?: string;
    },
): string {
    return `${item.label} (${item.value})`;
}

function processEntries(entries: HitsPerGroupEntryModel[]) {
    const result: PieValueType[] = [];
    entries.map((e) => {
        result.push({
            id: `${e.name}_id`,
            value: e.hitsCount,
            label: e.name,
        });
    });
    // return it sorted small to large
    return result.sort(function (a, b) {
        if (a.value < b.value) return -1;
        return a.value == b.value ? 0 : 1;
    });
}

function summarizeEntries(entries: PieValueType[], max: number) {
    if (entries.length <= max) return { data: entries, others: [] };
    const result: PieValueType[] = [];
    const others: PieValueType[] = [];
    entries.toReversed().forEach((e) => {
        if (result.length < max - 1) result.push(e);
        else others.push(e);
    });
    result.unshift({
        id: MISC_ID,
        value: others.length,
        label: "others",
    } satisfies PieValueType);
    return { data: result.reverse(), others }; // small to large
}

export const Chart = ({
    entries,
    title,
    handleUpdateQuery,
    queryKeyword,
    compact,
}: ChartProps) => {
    const dataAll = processEntries(entries);
    const { data, others } = summarizeEntries(dataAll, compact);

    const handleClick = (
        _: any,
        __: PieItemIdentifier,
        item: DefaultizedPieValueType,
    ) => {
        let term: string;
        if (item.id === MISC_ID) {
            term = `(${others
                .filter((d) => d.label)
                .map((d) => `"${d.label}"`)
                .join(" OR ")})`;
        } else {
            term = item.label ? `"${item.label}"` : "";
        }
        handleUpdateQuery(queryKeyword, term);
    };

    return (
        <Fragment>
            <center>
                <Typography variant="h4">
                    {title} ({entries.length})
                </Typography>
            </center>
            {entries && (
                <PieChart
                    height={500}
                    onItemClick={handleClick}
                    colors={COLORS}
                    series={[
                        {
                            data,
                            arcLabel,
                            arcLabelMinAngle: 45,
                            highlightScope: {
                                faded: "global",
                                highlighted: "item",
                            },
                            faded: {
                                innerRadius: 30,
                                additionalRadius: -30,
                                color: "gray",
                            },
                        },
                    ]}
                />
            )}
        </Fragment>
    );
};
