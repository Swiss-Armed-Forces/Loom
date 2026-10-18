import { useCallback, useMemo } from "react";

import { GetFilePreviewResponse } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectAvailablePreviewFields,
    selectCardElementVisibility,
    selectFieldLayout,
    selectPreviewFields,
    selectQuery,
    updateQuery,
} from "@app/slices/searchSlice";
import {
    nextSortSelection,
    updateFieldOfQuery,
} from "@features/common/utils/helpers";
import { FieldItem } from "@features/search/components/FieldList/FieldItem";
import { FieldLine } from "@features/search/components/FieldList/FieldLine";
import { FieldList } from "@features/search/components/FieldList/FieldList";
import { FieldRow } from "@features/search/components/FieldList/FieldRow";

export interface FieldSectionsProps {
    filePreview: GetFilePreviewResponse;
    fullDetails?: boolean;
}

export const FieldSections = ({
    filePreview,
    fullDetails,
}: FieldSectionsProps) => {
    const dispatch = useAppDispatch();
    const query = useAppSelector(selectQuery);
    const previewFields = useAppSelector(selectPreviewFields);
    const availableFields = useAppSelector(selectAvailablePreviewFields);
    const { showHighlights, showFieldActions } = useAppSelector(
        selectCardElementVisibility,
    );
    const fieldLayout = useAppSelector(selectFieldLayout);
    // Full details wants the verbose, always-expanded form of every field.
    const compact = fieldLayout === "compact" && !fullDetails;
    const line = fieldLayout === "line" && !fullDetails;

    const responseFields = useMemo(
        () => filePreview.fields ?? {},
        [filePreview.fields],
    );
    const highlights = useMemo(
        () => (filePreview.highlight ?? {}) as Record<string, string[]>,
        [filePreview.highlight],
    );

    const labelFor = useMemo(() => {
        const map: Record<string, string> = {};
        for (const f of availableFields) {
            map[f.id] = f.label;
        }
        return map;
    }, [availableFields]);

    const selectedEntries = useMemo(
        () =>
            previewFields
                .filter((id) => responseFields[id] != null)
                .map((id) => ({ id, label: labelFor[id] ?? id })),
        [previewFields, responseFields, labelFor],
    );

    // Every selected field takes its column, including the ones this file has
    // no value for: a skipped cell would shift the rest of the card's line out
    // of line with the column header and with every other card.
    const lineCells = useMemo(
        () =>
            previewFields.map((id) => ({
                id,
                label: labelFor[id] ?? id,
                value: responseFields[id]?.value ?? "",
            })),
        [previewFields, responseFields, labelFor],
    );

    const handleQuery = useCallback(
        (
            fieldId: string,
            value: string,
            negate: boolean,
            accumulate: boolean,
        ) => {
            dispatch(
                updateQuery({
                    query: updateFieldOfQuery(
                        query?.query ?? "",
                        fieldId,
                        value,
                        false,
                        negate,
                        accumulate,
                    ),
                }),
            );
        },
        [dispatch, query],
    );

    // Same rule as the column header: asking again for the field already
    // sorted reverses it, and the direction written here is the one the
    // search bar's direction toggle shows.
    const handleSort = useCallback(
        (fieldId: string) => {
            dispatch(updateQuery(nextSortSelection(query, fieldId)));
        },
        [dispatch, query],
    );

    const highlightList = showHighlights &&
        Object.keys(highlights).length > 0 && (
            <FieldList
                highlights={highlights}
                fullDetails={fullDetails}
                showActions={showFieldActions || !!fullDetails}
            />
        );

    // One line for the whole card: the fields are read by position, so they
    // are drawn together rather than one renderer call per field.
    if (line) {
        return (
            <>
                <FieldLine cells={lineCells} />
                {highlightList}
            </>
        );
    }

    return (
        <>
            {selectedEntries.map(({ id, label }) => {
                const fieldData = responseFields[id]!;
                const value = fieldData.isTruncated
                    ? [fieldData.value + "…"]
                    : [fieldData.value];
                const actionsShown = showFieldActions || fullDetails;
                const onQuery = actionsShown
                    ? (negate: boolean, accumulate: boolean) =>
                          handleQuery(id, fieldData.value, negate, accumulate)
                    : undefined;
                const onSort = actionsShown ? () => handleSort(id) : undefined;
                // An expand control only earns its place on a value the
                // backend actually cut short - everything else is one line.
                if (compact && !fieldData.isTruncated) {
                    return (
                        <FieldRow
                            key={id}
                            field={label}
                            value={fieldData.value}
                            onQuery={onQuery}
                            onSort={onSort}
                        />
                    );
                }
                return (
                    <FieldItem
                        key={id}
                        field={label}
                        fieldKey={id}
                        value={value}
                        onQuery={onQuery}
                        onSort={onSort}
                        fullDetails={fullDetails}
                        disableDivider={compact}
                    />
                );
            })}
            {highlightList}
        </>
    );
};
