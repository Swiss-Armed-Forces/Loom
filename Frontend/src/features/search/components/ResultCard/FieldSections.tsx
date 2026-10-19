import { memo, useCallback, useMemo } from "react";

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

export const FieldSections = memo(
    ({ filePreview, fullDetails }: FieldSectionsProps) => {
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

        // `value` is an array prop, so it is built here and memoised with the
        // response rather than rebuilt per render, which would defeat FieldItem's
        // memo on every pass.
        const selectedEntries = useMemo(
            () =>
                previewFields
                    .filter((id) => responseFields[id] != null)
                    .map((id) => {
                        const fieldData = responseFields[id]!;
                        return {
                            id,
                            label: labelFor[id] ?? id,
                            isTruncated: fieldData.isTruncated ?? false,
                            text: fieldData.value,
                            value: fieldData.isTruncated
                                ? [fieldData.value + "…"]
                                : [fieldData.value],
                        };
                    }),
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

        // One handler for the whole list rather than a closure per field, so the
        // memoised FieldItem can bail out. It resolves the value from the field id
        // the item reports back.
        const handleQuery = useCallback(
            (fieldId: string, negate: boolean, accumulate: boolean) => {
                const value = responseFields[fieldId]?.value;
                if (value === undefined) return;
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
            [dispatch, query, responseFields],
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
                {selectedEntries.map(
                    ({ id, label, isTruncated, text, value }) => {
                        const actionsShown = showFieldActions || fullDetails;
                        // An expand control only earns its place on a value the
                        // backend actually cut short - everything else is one line.
                        if (compact && !isTruncated) {
                            // FieldRow is not memoised, so a closure per row costs it
                            // nothing; FieldItem below is, and takes the shared
                            // handler instead.
                            return (
                                <FieldRow
                                    key={id}
                                    field={label}
                                    value={text}
                                    onQuery={
                                        actionsShown
                                            ? (negate, accumulate) =>
                                                  handleQuery(
                                                      id,
                                                      negate,
                                                      accumulate,
                                                  )
                                            : undefined
                                    }
                                    onSort={
                                        actionsShown
                                            ? () => handleSort(id)
                                            : undefined
                                    }
                                />
                            );
                        }
                        return (
                            <FieldItem
                                key={id}
                                field={label}
                                fieldKey={id}
                                value={value}
                                onQuery={actionsShown ? handleQuery : undefined}
                                onSort={actionsShown ? handleSort : undefined}
                                fullDetails={fullDetails}
                                disableDivider={compact}
                            />
                        );
                    },
                )}
                {highlightList}
            </>
        );
    },
);

FieldSections.displayName = "FieldSections";
