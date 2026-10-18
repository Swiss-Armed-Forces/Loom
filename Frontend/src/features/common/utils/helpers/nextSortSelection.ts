import { SearchQuery, SortDirection } from "@features/common/utils/model";

/** The field and direction a sort control is asking the query to take. */
export interface SortSelection {
    sortField: string;
    sortDirection: SortDirection;
}

/** What an unsorted query sorts by first. Dates, sizes and scores are all
 *  read from the top, so the useful end comes first. */
const FIRST_DIRECTION: SortDirection = "desc";

/**
 * The sort that asking for `field` produces.
 *
 * A field that is not the current sort starts at `FIRST_DIRECTION`. Asking
 * again for the field already sorted reverses it, which is how a control with
 * nothing but the field itself to click - a column header, a per-field sort
 * button - says "the other end".
 *
 * The direction lives in the query, so every control that writes it through
 * this function stays in step with the sort direction toggle in the search
 * bar, which reads and writes the same field.
 */
export const nextSortSelection = (
    query: SearchQuery | null,
    field: string,
): SortSelection => {
    const reverses =
        query?.sortField === field &&
        (query.sortDirection ?? FIRST_DIRECTION) === FIRST_DIRECTION;
    return {
        sortField: field,
        sortDirection: reverses ? "asc" : FIRST_DIRECTION,
    };
};
