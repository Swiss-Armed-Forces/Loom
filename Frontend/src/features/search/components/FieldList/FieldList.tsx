import { useMemo, useCallback } from "react";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { updateQuery, selectQuery } from "@app/slices/searchSlice";
import { updateFieldOfQuery } from "@features/common/utils/helpers";

import { FieldItem } from "./FieldItem";

type HighlightEntry = [string, string[]];
const STRIP_TAGS = /<\/?highlight>/g;

const PRIORITIES = [
    /^full_name$/,
    /^short_name$/,
    /^content/,
    /^translations/,
    null, // Fallback for unmatched fields
    /^tika_meta/,
    /^tasks/,
];

const getHighlightPriority = (key: string): number => {
    let fallbackPrio = 9999;
    for (let i = 0; i < PRIORITIES.length; i++) {
        const prio = PRIORITIES[i];
        if (prio === null) fallbackPrio = i;
        else if (prio.test(key)) return i;
    }
    return fallbackPrio;
};

const sortHighlightsByPriority = (
    a: HighlightEntry,
    b: HighlightEntry,
): number => {
    const aPrio = getHighlightPriority(a[0]);
    const bPrio = getHighlightPriority(b[0]);
    return aPrio !== bPrio ? aPrio - bPrio : a[0].localeCompare(b[0]);
};

export interface FieldListProps {
    highlights: Record<string, string[]>;
    fullDetails?: boolean;
    showActions?: boolean;
}

export const FieldList = ({
    highlights,
    fullDetails,
    showActions = true,
}: FieldListProps) => {
    const dispatch = useAppDispatch();
    const query = useAppSelector(selectQuery);

    // Sort highlights only when data changes
    const sortedEntries = useMemo(
        () => Object.entries(highlights ?? {}).sort(sortHighlightsByPriority),
        [highlights],
    );

    // Pre-calculate clean values for search queries
    const cleanValues = useMemo(() => {
        const mapping: Record<string, string> = {};
        Object.entries(highlights ?? {}).forEach(([field, val]) => {
            mapping[field] = val[0]?.replace(STRIP_TAGS, "") ?? "";
        });
        return mapping;
    }, [highlights]);

    const handleQuery = useCallback(
        (field: string, negate: boolean) => {
            dispatch(
                updateQuery({
                    query: updateFieldOfQuery(
                        query?.query ?? "",
                        field,
                        cleanValues[field],
                        false,
                        negate,
                    ),
                }),
            );
        },
        [dispatch, query, cleanValues],
    );

    const handleSort = useCallback(
        (field: string) => {
            dispatch(updateQuery({ sortField: field }));
        },
        [dispatch],
    );

    if (!highlights) return null;

    return (
        <>
            {sortedEntries.map(([field, value]) => (
                <FieldItem
                    key={field}
                    field={field}
                    value={value}
                    onQuery={
                        showActions
                            ? (negate) => handleQuery(field, negate)
                            : undefined
                    }
                    onSort={showActions ? () => handleSort(field) : undefined}
                    fullDetails={fullDetails}
                />
            ))}
        </>
    );
};
