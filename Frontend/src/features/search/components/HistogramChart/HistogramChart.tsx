import { BarChart } from "@mui/x-charts/BarChart";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";
import { BarItemIdentifier } from "@mui/x-charts/models";
import React, { useMemo, useState } from "react";

import { GroupedHitsPerGroupEntryModel } from "@app/api";

import {
    CHART_COLORS,
    NONE_LABEL,
    OTHERS_COLOR,
    OTHERS_LABEL,
} from "../chartColors";

interface HistogramChartProps {
    groupedEntries?: GroupedHitsPerGroupEntryModel[] | null;
    onRangeSelect?: (startDate: string, endDate: string) => void;
    /** Called when the user clicks a bar segment; emits the group name (or list of named groups for "others") and whether to negate. */
    onGroupFilter?: (
        group: string | string[],
        negate: boolean,
        noQuote?: boolean,
    ) => void;
    height?: number;
    /**
     * Group names in pie-chart color-index order (index 0 → CHART_COLORS[0],
     * etc.). When provided, bar-chart segments are colored by name-lookup so
     * they match the pie chart regardless of which groups appear in the date
     * buckets. The color at index groupColorOrder.length is used for "others".
     */
    groupColorOrder?: string[];
    /** Whether bucket keys are dates ("date") or raw numbers ("number"). */
    chartType?: "date" | "number";
    /** Group name currently hovered in the pie chart; highlights the matching series. */
    highlightedGroup?: string | null;
    /** Called when the user hovers a bar segment; emits the series (group) name or null. */
    onGroupHighlight?: (group: string | null) => void;
    /**
     * Index offset applied to CHART_COLORS lookups so bar colors match the pie.
     * Pass 1 when the pie chart has an "others" slice (which occupies index 0).
     */
    colorOffset?: number;
}

const ONE_YEAR_MS = 365 * 24 * 60 * 60 * 1000;
const ONE_MONTH_MS = 30 * 24 * 60 * 60 * 1000;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
const ONE_HOUR_MS = 60 * 60 * 1000;

const COLOR_OTHERS = "#b0bec5";

type BandScale = ((value: string) => number | undefined) & {
    bandwidth(): number;
};

/**
 * Invisible rect over the x-axis label area. Calls onHover with the bucket
 * index when the cursor enters a bucket's column in the axis zone, or null
 * when the cursor leaves. Used to restrict range-selection ghost markers to
 * the axis label area only (not over bars).
 */
/**
 * Self-contained overlay rendered inside the BarChart SVG.
 * Keeps its own hoverBucket state so mouse-move re-renders stay local
 * and never cause the parent HistogramChart (or BarChart) to re-render.
 */
const RangeSelectionOverlay = ({
    xLabels,
    selectionStart,
    onAxisClick,
    onSelectionReset,
}: {
    xLabels: string[];
    selectionStart: number | null;
    onAxisClick: (bucket: number) => void;
    onSelectionReset: () => void;
}) => {
    const [hoverBucket, setHoverBucket] = useState<number | null>(null);
    const { left, top, width, height, bottom } = useDrawingArea();
    const xScale = useXScale() as unknown as BandScale;

    // Snap to the nearest bucket — covers inter-band padding with no null gaps.
    const bucketAt = (e: React.MouseEvent<SVGRectElement>): number | null => {
        if (xLabels.length === 0) return null;
        const svgEl = e.currentTarget.closest("svg");
        if (!svgEl) return null;
        const { left: svgLeft } = svgEl.getBoundingClientRect();
        const svgX = e.clientX - svgLeft;
        const bw = xScale.bandwidth();
        let best = 0;
        let bestDist = Infinity;
        for (let i = 0; i < xLabels.length; i++) {
            const x = xScale(xLabels[i]);
            if (x === undefined) continue;
            const dist = Math.abs(svgX - (x + bw / 2));
            if (dist < bestDist) {
                bestDist = dist;
                best = i;
            }
        }
        return best;
    };

    const hover = hoverBucket;
    const start = selectionStart;

    // Labels on the same side as the drag direction so they stay readable.
    // When start ≤ end (or ghost): both labels on the right.
    // When start > end: both labels on the left.
    const endIdx =
        start !== null && hover !== null ? hover : (hover ?? start ?? 0);
    const leftward = start !== null && hover !== null && hover < start;

    if (bottom <= 0) return null;

    return (
        <>
            {/* Invisible rect over axis label zone — hover + click for range selection */}
            <rect
                x={left}
                y={top + height}
                width={width}
                height={bottom}
                fill="transparent"
                style={{ cursor: "pointer" }}
                onMouseMove={(e) => setHoverBucket(bucketAt(e))}
                onMouseLeave={() => setHoverBucket(null)}
                onClick={(e) => {
                    const b = bucketAt(e);
                    if (b !== null) onAxisClick(b);
                }}
                onContextMenu={(e) => {
                    e.preventDefault();
                    onSelectionReset();
                }}
            />

            {/* Ghost: no selection yet, cursor over axis — centered on the bar */}
            {start === null &&
                hover !== null &&
                (() => {
                    const bx = xScale(xLabels[hover]);
                    if (bx === undefined) return null;
                    const cx = bx + xScale.bandwidth() / 2;
                    return (
                        <>
                            <line
                                x1={cx}
                                y1={top}
                                x2={cx}
                                y2={top + height}
                                stroke="rgba(25, 118, 210, 0.35)"
                                strokeWidth={1.5}
                                strokeDasharray="4 3"
                                pointerEvents="none"
                            />
                            <text
                                x={cx + 4}
                                y={top + 14}
                                fill="rgba(25, 118, 210, 0.4)"
                                fontSize={11}
                            >
                                start
                            </text>
                        </>
                    );
                })()}

            {/* Active selection: range highlight + start + end markers.
                Lines are placed at the outer edge of their respective bars
                using pixel math (bandwidth) so the last bar is handled
                correctly — the domain-value trick xLabels[i+1] has no
                fallback for the last bar.
                - start bar: left edge when dragging right, right edge when dragging left
                - end bar:   right edge when dragging right, left edge when dragging left */}
            {start !== null &&
                (() => {
                    const lo = Math.min(start, endIdx);
                    const hi = Math.max(start, endIdx);
                    const bw = xScale.bandwidth();
                    const startBarX = xScale(xLabels[start]);
                    const endBarX = xScale(xLabels[endIdx]);
                    if (startBarX === undefined || endBarX === undefined)
                        return null;
                    const startLineX = leftward ? startBarX + bw : startBarX;
                    const endLineX = leftward ? endBarX : endBarX + bw;
                    const labelAnchor = leftward
                        ? ("end" as const)
                        : ("start" as const);
                    const labelDx = leftward ? -4 : 4;
                    return (
                        <>
                            <RangeHighlight
                                startLabel={xLabels[lo]}
                                endLabel={xLabels[hi]}
                            />
                            <line
                                x1={startLineX}
                                y1={top}
                                x2={startLineX}
                                y2={top + height}
                                stroke="rgba(25, 118, 210, 0.8)"
                                strokeWidth={2}
                                strokeDasharray="4 3"
                                pointerEvents="none"
                            />
                            <text
                                x={startLineX + labelDx}
                                y={top + 14}
                                fill="rgba(25, 118, 210, 0.9)"
                                fontSize={11}
                                fontWeight={600}
                                textAnchor={labelAnchor}
                            >
                                start
                            </text>
                            <line
                                x1={endLineX}
                                y1={top}
                                x2={endLineX}
                                y2={top + height}
                                stroke="rgba(25, 118, 210, 0.5)"
                                strokeWidth={1.5}
                                strokeDasharray="4 3"
                                pointerEvents="none"
                            />
                            <text
                                x={endLineX + labelDx}
                                y={start === endIdx ? top + 26 : top + 14}
                                fill="rgba(25, 118, 210, 0.7)"
                                fontSize={11}
                                textAnchor={labelAnchor}
                            >
                                end
                            </text>
                        </>
                    );
                })()}
        </>
    );
};

/** Renders a semi-transparent highlight rect spanning from startLabel to endLabel (inclusive). */
const RangeHighlight = ({
    startLabel,
    endLabel,
    alpha = 0.15,
}: {
    startLabel: string;
    endLabel: string;
    alpha?: number;
}) => {
    const { top, height } = useDrawingArea();
    const xScale = useXScale() as unknown as BandScale;
    const x0 = xScale(startLabel);
    const x1 = xScale(endLabel);
    if (x0 === undefined || x1 === undefined) return null;
    const left = Math.min(x0, x1);
    const right = Math.max(x0, x1) + xScale.bandwidth();
    return (
        <rect
            x={left}
            y={top}
            width={right - left}
            height={height}
            fill={`rgba(25, 118, 210, ${alpha})`}
            pointerEvents="none"
        />
    );
};

const formatDateLabel = (dateStr: string, rangeMs: number): string => {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    if (rangeMs >= ONE_YEAR_MS) {
        return date.getFullYear().toString();
    } else if (rangeMs >= ONE_MONTH_MS) {
        return date.toLocaleDateString(undefined, {
            month: "short",
            year: "numeric",
        });
    } else if (rangeMs >= ONE_DAY_MS) {
        return date.toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
        });
    } else if (rangeMs >= ONE_HOUR_MS) {
        return date.toLocaleString(undefined, {
            month: "short",
            day: "numeric",
            hour: "2-digit",
        });
    }
    return date.toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
    });
};

/**
 * Returns the top-N group keys sorted ascending by total count (least-common
 * first among the top groups), matching the color-assignment order of Chart.tsx.
 */
const topGroups = (
    grouped: GroupedHitsPerGroupEntryModel[],
    maxGroups: number,
): string[] => {
    const totals: Record<string, number> = {};
    for (const bucket of grouped) {
        for (const [key, count] of Object.entries<number>(bucket.groups)) {
            totals[key] = (totals[key] ?? 0) + count;
        }
    }
    return Object.entries(totals)
        .sort((a, b) => b[1] - a[1]) // descending to pick the top groups
        .slice(0, maxGroups)
        .reverse() // ascending so color indices match the pie chart
        .map(([key]) => key);
};

export const HistogramChart = ({
    groupedEntries,
    onRangeSelect,
    onGroupFilter,
    height = 500,
    groupColorOrder,
    chartType = "date",
    highlightedGroup,
    onGroupHighlight,
    colorOffset = 0,
}: HistogramChartProps) => {
    const [selectionStart, setSelectionStart] = useState<number | null>(null);

    const isNumber = chartType === "number";
    const items = groupedEntries ?? [];

    const timestamps = isNumber
        ? []
        : items.map((e) => new Date(e.name).getTime()).filter((t) => !isNaN(t));
    const rangeMs =
        timestamps.length >= 2
            ? Math.max(...timestamps) - Math.min(...timestamps)
            : 0;

    const xLabels = isNumber
        ? items.map((e) => Number(e.name).toLocaleString())
        : items.map((e) => formatDateLabel(e.name, rangeMs));

    const getEndValue = (hi: number): string | null => {
        if (isNumber) {
            if (hi + 1 < items.length) {
                return items[hi + 1].name;
            }
            if (items.length >= 2) {
                const last = Number(items[items.length - 1].name);
                const prev = Number(items[items.length - 2].name);
                return String(last + (last - prev));
            }
            return null;
        }
        if (hi + 1 < items.length) {
            return items[hi + 1].name;
        }
        // Last bucket: estimate its end by adding one bucket interval.
        if (items.length >= 2) {
            const lastMs = new Date(items[items.length - 1].name).getTime();
            const prevMs = new Date(items[items.length - 2].name).getTime();
            return new Date(lastMs + (lastMs - prevMs)).toISOString();
        }
        // Single bucket: can't determine a bounded end, don't filter.
        return null;
    };

    // Axis-label click: range selection (two-click flow, only from RangeSelectionOverlay).
    const handleAxisBucketClick = (idx: number) => {
        if (selectionStart === null) {
            setSelectionStart(idx);
        } else {
            const lo = Math.min(selectionStart, idx);
            const hi = Math.max(selectionStart, idx);
            const endValue = getEndValue(hi);
            if (endValue !== null) {
                onRangeSelect!(items[lo].name, endValue);
            }
            setSelectionStart(null);
        }
    };

    // Bar-segment click: group filter (immediate, no two-click flow).
    const handleItemClick = (event: MouseEvent, d: BarItemIdentifier) => {
        if (!onGroupFilter) return;
        const group = d.seriesId as string;
        if (group === OTHERS_LABEL) {
            // Mirror pie chart: click → exclude named (show only others),
            // shift-click → include only named (exclude others).
            const namedGroups = series
                .filter((s) => s.id !== OTHERS_LABEL)
                .map((s) => s.label);
            onGroupFilter(namedGroups, !event.shiftKey);
        } else if (group === NONE_LABEL) {
            // "(none)" = field absent. Normal click → NOT field:* (no field set),
            // shift-click → field:* (field exists), i.e. the inverse.
            onGroupFilter("*", !event.shiftKey, true);
        } else {
            onGroupFilter(group, event.shiftKey);
        }
    };

    const hint = onRangeSelect
        ? selectionStart !== null
            ? `From: ${xLabels[selectionStart]} — click to confirm end, right-click to cancel`
            : `Click axis label to start ${isNumber ? "range" : "date range"} selection`
        : null;

    // --- Build series ---
    // Rendering is bounded: auto_date_histogram caps at 24 buckets, and the
    // sub-aggregation size is capped at 100 groups per bucket (see
    // file_repository.py). MUI X BarChart renders synchronously without
    // virtualisation, but 24 × 100 is well within acceptable range.
    // Max named groups = number of groups the pie chart shows (excl. "others").
    // Fall back to 4 if no color order is provided.
    const MAX_GROUPS = groupColorOrder?.length ?? 4;
    const useGrouped = items.length > 0;

    // Resolve the color for a named group: look it up by name in groupColorOrder
    // so it matches the pie chart, falling back to a positional color.
    const groupColor = (group: string, fallbackIdx: number): string => {
        const idx = groupColorOrder
            ? groupColorOrder.indexOf(group)
            : fallbackIdx;
        return (
            CHART_COLORS[(idx >= 0 ? idx : fallbackIdx) + colorOffset] ??
            COLOR_OTHERS
        );
    };
    // When the pie has an "others" slice (colorOffset > 0), that slice sits at
    // CHART_COLORS[0]. Use the same color for the histogram's "others" bar.
    const othersColor =
        colorOffset > 0
            ? OTHERS_COLOR
            : (CHART_COLORS[MAX_GROUPS] ?? COLOR_OTHERS);

    const highlightScope = {
        highlight: "series",
        fade: "global",
    } as const;

    const groups = useMemo(
        () => groupColorOrder ?? topGroups(groupedEntries ?? [], MAX_GROUPS),
        [groupColorOrder, groupedEntries, MAX_GROUPS],
    );
    const othersData = useMemo(
        () =>
            (groupedEntries ?? []).map((b) => {
                const topSum = groups.reduce(
                    (s, g) => s + (b.groups[g] ?? 0),
                    0,
                );
                const totalGroupSum = Object.values<number>(b.groups).reduce(
                    (s, v) => s + v,
                    0,
                );
                return Math.max(0, totalGroupSum - topSum);
            }),
        [groupedEntries, groups],
    );

    let series: {
        id: string;
        data: (number | null)[];
        label: string;
        color: string;
        stack: string;
        highlightScope: typeof highlightScope;
    }[];

    if (useGrouped) {
        // Use the pie chart's group order when available so both charts show
        // identical named groups and compute "others" consistently.
        series = groups.map((group, i) => ({
            id: group,
            label: group,
            color: groupColor(group, i),
            stack: "total",
            highlightScope,
            data: groupedEntries!.map((b) => b.groups[group] ?? 0),
        }));

        // "others" series: always registered so MUI X Charts never throws when
        // the highlighted group is "others" and stats refresh removes it.
        // Buckets with 0 overflow use null so MUI skips rendering and tooltips.
        // Using the sum of returned groups (not hitsCount) handles multi-value
        // fields like tags where one document contributes to multiple buckets,
        // which makes topSum > hitsCount and the hitsCount-based formula wrong.
        series.push({
            id: OTHERS_LABEL,
            label: OTHERS_LABEL,
            color: othersColor,
            stack: "total",
            highlightScope,
            data: othersData.map((v) => (v > 0 ? v : null)),
        });
    } else {
        series = [
            {
                id: "count",
                label: "count",
                color: CHART_COLORS[0],
                stack: "total",
                highlightScope,
                data: items.map((e) => e.hitsCount),
            },
        ];
    }

    return (
        <div style={{ width: "100%" }}>
            <BarChart
                height={height}
                xAxis={[
                    {
                        data: xLabels,
                        scaleType: "band",
                        tickLabelStyle: { fontSize: 10 },
                    },
                ]}
                yAxis={[{ tickMinStep: 1 }]}
                series={series}
                highlightedItem={
                    highlightedGroup !== null &&
                    highlightedGroup !== undefined &&
                    series.some((s) => s.id === highlightedGroup)
                        ? { seriesId: highlightedGroup }
                        : null
                }
                onHighlightChange={(item) =>
                    onGroupHighlight?.(item ? (item.seriesId as string) : null)
                }
                onItemClick={onGroupFilter ? handleItemClick : undefined}
                slotProps={{ tooltip: { trigger: "item" } }}
                hideLegend
                sx={onGroupFilter ? { cursor: "pointer" } : undefined}
            >
                {onRangeSelect && (
                    <RangeSelectionOverlay
                        xLabels={xLabels}
                        selectionStart={selectionStart}
                        onAxisClick={handleAxisBucketClick}
                        onSelectionReset={() => setSelectionStart(null)}
                    />
                )}
            </BarChart>
            {hint && (
                <div
                    style={{
                        fontSize: 11,
                        opacity: 0.6,
                        textAlign: "center",
                        marginTop: 4,
                    }}
                >
                    {hint}
                </div>
            )}
        </div>
    );
};
