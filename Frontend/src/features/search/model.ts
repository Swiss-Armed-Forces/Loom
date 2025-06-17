import {
    GenericStatisticsModel,
    LibretranslateSupportedLanguages,
    SummaryStatisticsModel,
} from "../../app/api";

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

export interface FileDialogDetailData {
    fileId: string;
    tab?: FileDetailViewTab;
}
export enum FileDetailViewTab {
    Content,
    Highlights,
    RAW,
    Summary,
}

export interface CombinedStats {
    summary: SummaryStatisticsModel | null;
    generic: GenericStatisticsModel | null;
    tags: GenericStatisticsModel | null;
}
