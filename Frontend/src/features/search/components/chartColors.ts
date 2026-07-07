import { HitsPerGroupEntryModel } from "@app/api";

export const CHART_COLORS = [
    "#0088FE",
    "#00C49F",
    "#FFBB28",
    "#FF8042",
    "#d32f2f",
    "#7b1fa2",
    "#5d4037",
    "#455a64",
];

/** Label used for the "others" slice/series in both the pie and histogram charts. */
export const OTHERS_LABEL = "others";

/** Label used for documents where the grouped field is absent. */
export const NONE_LABEL = "(none)";

/** Color assigned to the "others" slice/series — always the first chart color. */
export const OTHERS_COLOR = CHART_COLORS[0];

/**
 * Number of documents not represented by the named entries.
 * Used to determine whether an "others" slice/bar should be shown.
 */
export const computeOthersCount = (
    entries: HitsPerGroupEntryModel[],
    fileCount: number,
): number =>
    Math.max(0, fileCount - entries.reduce((s, e) => s + e.hitsCount, 0));
