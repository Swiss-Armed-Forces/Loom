import {
    GenericStatisticsModel,
    LibretranslateSupportedLanguages,
    SortId,
    SummaryStatisticsModel,
} from "../../app/api";

export interface TreeExpandedState {
    path: string;
    isExpanded: boolean;
}

export const sortDirections = ["asc", "desc"] as const;
export type SortDirection = (typeof sortDirections)[number];
export function isSortDirection(x: string): x is SortDirection {
    return (sortDirections as readonly string[]).indexOf(x) >= 0;
}

export interface SearchQuery {
    query?: string | null;
    languages?: LibretranslateSupportedLanguages[] | null;
    sortField?: string | null;
    sortDirection?: SortDirection | null;
    sortId?: SortId | null;
    pageSize?: number | null;
}
export function getSearchParamsFromSearchQuery(
    query: SearchQuery,
): URLSearchParams {
    const searchParams = new URLSearchParams({
        ...(query.query && { search_string: query.query }),
        ...(query.sortField && {
            sort_by_field: query.sortField,
        }),
        ...(query.sortDirection && {
            sort_direction: query.sortDirection,
        }),
        ...(query.sortId && {
            sort_id: query.sortId.toString(),
        }),
        ...(query.pageSize != null && {
            page_size: query.pageSize.toString(),
        }),
    });
    query.languages?.forEach((l) =>
        searchParams.append("search_languages", l.code),
    );
    return searchParams;
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
