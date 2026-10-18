import {
    GroupedHistogramStatisticsModel,
    TermsStatisticsModel,
} from "@app/api";

import { DialogType } from "./enums";

export interface TreeExpandedState {
    path: string;
    isExpanded: boolean;
}

export interface Point {
    x: number;
    y: number;
}

export interface Size {
    width: number;
    height: number;
}

export const sortDirections = ["asc", "desc"] as const;
export type SortDirection = (typeof sortDirections)[number];
export const isSortDirection = (x: string): x is SortDirection => {
    return (sortDirections as readonly string[]).includes(x);
};

export interface SearchQuery {
    id: string | null;
    query: string;
    keepAlive: "10s" | "30m" | null;
    sortField: string | null;
    sortDirection: SortDirection | null;
    sortId: any[] | null;
    pageSize: number | null;
}

/**
 * A query that has a point-in-time, which the paginated endpoints require.
 *
 * Their pages resume from literal sort values that only mean anything inside the
 * snapshot that produced them, so the backend rejects a request without one. Callers
 * narrow to this by checking `id`, which is also what stops a page being requested
 * before the snapshot has been opened.
 */
export type PitBoundSearchQuery = SearchQuery & { id: string };

export interface CombinedStats {
    termsData: TermsStatisticsModel | null;
    histogramData: GroupedHistogramStatisticsModel | null;
}

export interface DialogComponent {
    id: string;
    type: DialogType;
    props?: Record<string, any>;
}
