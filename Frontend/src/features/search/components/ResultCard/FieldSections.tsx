import { Box } from "@mui/material";
import { memo, useCallback, useMemo } from "react";

import { GetFilePreviewResponse } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectAvailablePreviewFields,
    selectBoldPreviewFields,
    selectCardElementVisibility,
    selectFieldColumnCount,
    selectFieldColumnOf,
    selectShowFieldNames,
    selectFieldLayout,
    selectPreviewFields,
    selectQuery,
    updateQuery,
} from "@app/slices/searchSlice";
import {
    nextSortSelection,
    updateFieldOfQuery,
} from "@features/common/utils/helpers";
import { FieldIndicator } from "@features/search/components/FieldList/FieldIndicator";
import { FieldItem } from "@features/search/components/FieldList/FieldItem";
import { FieldLine } from "@features/search/components/FieldList/FieldLine";
import { FieldList } from "@features/search/components/FieldList/FieldList";
import { FieldRow } from "@features/search/components/FieldList/FieldRow";
import {
    isIndicatorField,
    useFieldLabels,
} from "@features/search/components/FieldList/indicatorFields";

export interface FieldSectionsProps {
    filePreview: GetFilePreviewResponse;
    fullDetails?: boolean;
}

/* Equal shares rather than content-sized columns: the columns are read
across, so a value has to start where the value above it did however long its
neighbour to the left runs. */
const COLUMNS_SX = {
    display: "flex",
    gap: 2,
    alignItems: "flex-start",
} as const;
const COLUMN_SX = { flex: "1 1 0", minWidth: 0 } as const;

export const FieldSections = memo(
    ({ filePreview, fullDetails }: FieldSectionsProps) => {
        const dispatch = useAppDispatch();
        const query = useAppSelector(selectQuery);
        const previewFields = useAppSelector(selectPreviewFields);
        const boldFields = useAppSelector(selectBoldPreviewFields);
        const columnCount = useAppSelector(selectFieldColumnCount);
        const columnOf = useAppSelector(selectFieldColumnOf);
        const availableFields = useAppSelector(selectAvailablePreviewFields);
        const { showHighlights, showFieldActions } = useAppSelector(
            selectCardElementVisibility,
        );
        const showFieldNames = useAppSelector(selectShowFieldNames);
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

        const labelFor = useFieldLabels(availableFields);

        // `value` is an array prop, so it is built here and memoised with the
        // response rather than rebuilt per render, which would defeat FieldItem's
        // memo on every pass.
        const selectedEntries = useMemo(
            () =>
                // Every selected field, whether or not this file has a value
                // for it. Skipping the empty ones makes a card's height depend
                // on the file rather than on the selection, which is what the
                // fixed row height is there to stop; an empty line also keeps
                // a card's fields under the same ones on the card above.
                previewFields.map((id) => {
                    const common = {
                        id,
                        label: labelFor[id] ?? id,
                        bold: boldFields.includes(id),
                        column: Math.min(columnOf[id] ?? 0, columnCount - 1),
                    };
                    if (isIndicatorField(id)) {
                        return {
                            ...common,
                            indicator: id,
                            isTruncated: false,
                            text: "",
                            value: [""],
                        };
                    }
                    const fieldData = responseFields[id];
                    const text = fieldData?.value ?? "";
                    return {
                        ...common,
                        indicator: null,
                        isTruncated: fieldData?.isTruncated ?? false,
                        text,
                        value: fieldData?.isTruncated ? [text + "…"] : [text],
                    };
                }),
            [
                previewFields,
                responseFields,
                labelFor,
                boldFields,
                columnOf,
                columnCount,
            ],
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
                    bold: boldFields.includes(id),
                    indicator: isIndicatorField(id) ? id : null,
                    preview: filePreview,
                })),
            [previewFields, responseFields, labelFor, boldFields, filePreview],
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

        const showNames = showFieldNames || Boolean(fullDetails);

        const renderEntry = ({
            id,
            label,
            bold,
            indicator,
            isTruncated,
            text,
            value,
        }: (typeof selectedEntries)[number]) => {
            if (indicator) {
                return (
                    <FieldIndicator
                        key={id}
                        fieldId={indicator}
                        filePreview={filePreview}
                        bold={bold}
                        showName={showNames}
                    />
                );
            }
            const actionsShown = showFieldActions || fullDetails;
            // An expand control only earns its place on a value the backend
            // actually cut short - everything else is one line.
            if (compact && !isTruncated) {
                // FieldRow is not memoised, so a closure per row costs it
                // nothing; FieldItem below is, and takes the shared handler
                // instead.
                return (
                    <FieldRow
                        key={id}
                        field={label}
                        value={text}
                        bold={bold}
                        showName={showNames}
                        onQuery={
                            actionsShown
                                ? (negate, accumulate) =>
                                      handleQuery(id, negate, accumulate)
                                : undefined
                        }
                        onSort={actionsShown ? () => handleSort(id) : undefined}
                    />
                );
            }
            return (
                <FieldItem
                    key={id}
                    field={label}
                    fieldKey={id}
                    value={value}
                    bold={bold}
                    showName={showNames}
                    onQuery={actionsShown ? handleQuery : undefined}
                    onSort={actionsShown ? handleSort : undefined}
                    fullDetails={fullDetails}
                    disableDivider={compact}
                />
            );
        };

        // One column is the card as it always was, so it is drawn flat rather
        // than as a single-column flex row. The detail panel reads top to
        // bottom and is never split.
        if (columnCount > 1 && !fullDetails) {
            return (
                <>
                    <Box sx={COLUMNS_SX}>
                        {Array.from({ length: columnCount }, (_, column) => (
                            <Box key={column} sx={COLUMN_SX}>
                                {selectedEntries
                                    .filter((e) => e.column === column)
                                    .map(renderEntry)}
                            </Box>
                        ))}
                    </Box>
                    {highlightList}
                </>
            );
        }

        return (
            <>
                {selectedEntries.map(renderEntry)}
                {highlightList}
            </>
        );
    },
);

FieldSections.displayName = "FieldSections";
