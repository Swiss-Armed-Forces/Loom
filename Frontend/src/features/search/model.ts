import {
    GenericStatisticsModel,
    LibretranslateSupportedLanguages,
    SummaryStatisticsModel,
} from "../../app/api";

import { JSONSchemaType } from "ajv";

export interface TreeExpandedState {
    path: string;
    isExpanded: boolean;
}

export const sortDirections = ["asc", "desc"] as const;
export type SortDirection = (typeof sortDirections)[number];
export function isSortDirection(x: string): x is SortDirection {
    return (sortDirections as readonly string[]).includes(x);
}

export interface SearchQuery {
    id: string;
    query: string;
    keepAlive: "10s" | "30m" | null;
    languages: LibretranslateSupportedLanguages[] | null;
    sortField: string | null;
    sortDirection: SortDirection | null;
    sortId: any[] | null;
    pageSize: number | null;
}

export const LibretranslateSupportedLanguagesSchema: JSONSchemaType<LibretranslateSupportedLanguages> =
    {
        type: "object",
        properties: {
            code: { type: "string" },
            name: { type: "string" },
        },
        required: ["code", "name"],
        additionalProperties: false,
    };

export const SearchQuerySchema = {
    type: "object",
    additionalProperties: false,
    properties: {
        id: { type: "string" },
        query: { type: "string" },

        keepAlive: { type: ["string", "null"], enum: ["10s", "30m", null] },

        languages: {
            type: ["array", "null"],
            items: LibretranslateSupportedLanguagesSchema,
        },

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
        "languages",
        "sortField",
        "sortDirection",
        "sortId",
        "pageSize",
    ],
} as const;

export enum FileDetailTab {
    Content,
    Highlights,
    RAW,
    Summary,
}

export interface FileDetailData {
    fileId: string;
    tab?: FileDetailTab;
}

export interface CombinedStats {
    summary: SummaryStatisticsModel | null;
    generic: GenericStatisticsModel | null;
    tags: GenericStatisticsModel | null;
}
