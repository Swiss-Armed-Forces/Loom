import { Box } from "@mui/material";
import { memo, useCallback, useMemo } from "react";

import { GetFilePreviewResponse } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectAvailablePreviewFields,
    selectStatePreviewFields,
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
import columnLayout from "@features/search/components/FieldList/columnLayout.module.css";
import { FieldIndicator } from "@features/search/components/FieldList/FieldIndicator";
import { FieldItem } from "@features/search/components/FieldList/FieldItem";
import { FieldLine } from "@features/search/components/FieldList/FieldLine";
import { FieldList } from "@features/search/components/FieldList/FieldList";
import { FieldRow } from "@features/search/components/FieldList/FieldRow";
import {
    isIndicatorField,
    useFieldLabels,
} from "@features/search/components/FieldList/indicatorFields";

import { fileStateStyle } from "./fileStateStyle";

export interface FieldSectionsProps {
    filePreview: GetFilePreviewResponse;
    fullDetails?: boolean;
}

export const FieldSections = memo(
    ({ filePreview, fullDetails }: FieldSectionsProps) => {
        const dispatch = useAppDispatch();
        const query = useAppSelector(selectQuery);
        const previewFields = useAppSelector(selectPreviewFields);
        const markedFields = useAppSelector(selectStatePreviewFields);
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

        // What a marked field is drawn as on this card. One object for the
        // whole card, so the memoised FieldItem sees the same prop on every
        // pass; see `fileStateStyle`.
        const { flagged, seen } = filePreview;
        const markedStyle = useMemo(
            () => fileStateStyle({ flagged, seen }),
            [flagged, seen],
        );

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
                        stateStyle: markedFields.includes(id)
                            ? markedStyle
                            : undefined,
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
                markedFields,
                markedStyle,
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
                    stateStyle: markedFields.includes(id)
                        ? markedStyle
                        : undefined,
                    indicator: isIndicatorField(id) ? id : null,
                    preview: filePreview,
                })),
            [
                previewFields,
                responseFields,
                labelFor,
                markedFields,
                markedStyle,
                filePreview,
            ],
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
            stateStyle,
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
                        stateStyle={stateStyle}
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
                        stateStyle={stateStyle}
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
                    stateStyle={stateStyle}
                    showName={showNames}
                    onQuery={actionsShown ? handleQuery : undefined}
                    onSort={actionsShown ? handleSort : undefined}
                    fullDetails={fullDetails}
                    disableDivider={compact}
                />
            );
        };

        // One column is the card as it always was, so it is drawn flat rather
        // than as a single-column grid. The detail panel reads top to
        // bottom and is never split.
        //
        // The tracks come from the list rather than from the card: the widths
        // the reader dragged in the strip above apply to every card, and a
        // card left to split itself evenly would ignore them.
        if (columnCount > 1 && !fullDetails) {
            return (
                <>
                    <Box className={columnLayout.compactGrid}>
                        {Array.from({ length: columnCount }, (_, column) => (
                            <Box
                                key={column}
                                className={columnLayout.compactColumn}
                            >
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
