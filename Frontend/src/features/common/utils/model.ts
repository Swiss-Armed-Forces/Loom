import {
    GroupedHistogramStatisticsModel,
    TermsStatisticsModel,
} from "@app/api";

import { DialogType } from "./enums";

export interface TreeExpandedState {
    path: string;
    isExpanded: boolean;
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

export const SearchQuerySchema = {
    type: "object",
    additionalProperties: false,
    properties: {
        id: { type: ["string", "null"] },
        query: { type: "string" },

        keepAlive: { type: ["string", "null"], enum: ["10s", "30m", null] },

        sortField: { type: ["string", "null"] },

        sortDirection: {
            type: ["string", "null"],
            enum: ["asc", "desc", null],
        },

        sortId: { type: ["array", "null"], items: {} },

        pageSize: { type: ["number", "null"] },
    },
    required: [
        "id",
        "query",
        "keepAlive",
        "sortField",
        "sortDirection",
        "sortId",
        "pageSize",
    ],
} as const;

export interface CombinedStats {
    termsData: TermsStatisticsModel | null;
    histogramData: GroupedHistogramStatisticsModel | null;
}

export interface DialogComponent {
    id: string;
    type: DialogType;
    props?: Record<string, any>;
}
