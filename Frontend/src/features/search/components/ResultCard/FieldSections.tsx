import { useCallback, useMemo } from "react";

import { GetFilePreviewResponse } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectAvailablePreviewFields,
    selectCardElementVisibility,
    selectPreviewFields,
    selectQuery,
    updateQuery,
} from "@app/slices/searchSlice";
import { updateFieldOfQuery } from "@features/common/utils/helpers";
import { FieldItem } from "@features/search/components/FieldList/FieldItem";
import { FieldList } from "@features/search/components/FieldList/FieldList";

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

    const handleSort = useCallback(
        (fieldId: string) => {
            dispatch(updateQuery({ sortField: fieldId }));
        },
        [dispatch],
    );

    return (
        <>
            {selectedEntries.map(({ id, label }) => {
                const fieldData = responseFields[id]!;
                const value = fieldData.isTruncated
                    ? [fieldData.value + "…"]
                    : [fieldData.value];
                return (
                    <FieldItem
                        key={id}
                        field={label}
                        fieldKey={id}
                        value={value}
                        onQuery={
                            showFieldActions || fullDetails
                                ? (negate, accumulate) =>
                                      handleQuery(
                                          id,
                                          fieldData.value,
                                          negate,
                                          accumulate,
                                      )
                                : undefined
                        }
                        onSort={
                            showFieldActions || fullDetails
                                ? () => handleSort(id)
                                : undefined
                        }
                        fullDetails={fullDetails}
                    />
                );
            })}
            {showHighlights && Object.keys(highlights).length > 0 && (
                <FieldList
                    highlights={highlights}
                    fullDetails={fullDetails}
                    showActions={showFieldActions || !!fullDetails}
                />
            )}
        </>
    );
};
