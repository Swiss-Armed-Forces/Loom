import { ArrowDownward, ArrowUpward } from "@mui/icons-material";
import { Box, ButtonBase, Tooltip, Typography } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectAvailablePreviewFields,
    selectCardElementVisibility,
    selectFieldColumnWidths,
    selectFieldLayout,
    selectPreviewFields,
    selectQuery,
    updateQuery,
} from "@app/slices/searchSlice";
import { nextSortSelection } from "@features/common/utils/helpers";
import { useFieldReorder } from "@features/search/hooks/useFieldReorder";

import styles from "./FieldColumnHeader.module.css";
import { reservesThumbnailSlot } from "./fieldColumns";
import { useColumnResize } from "./useColumnResize";

/**
 * Column labels for the line field layout, one per selected preview field.
 *
 * The labels are hoisted out of the cards and printed once at the top of the
 * list, which is what lets a card's line carry values alone. They stay put
 * while the list scrolls, so a column keeps its name however far down the
 * reader is, and each one sorts by its field - the line layout has no room
 * for a sort button per field per card.
 *
 * The header is built like a card's line and not merely to the same
 * measurements: the same grid, fed by the same variables, and the same
 * thumbnail slot beside it.
 */
export const FieldColumnHeader = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const previewFields = useAppSelector(selectPreviewFields);
    const availableFields = useAppSelector(selectAvailablePreviewFields);
    const columnWidths = useAppSelector(selectFieldColumnWidths);
    const fieldLayout = useAppSelector(selectFieldLayout);
    const visibility = useAppSelector(selectCardElementVisibility);
    const query = useAppSelector(selectQuery);
    const {
        gridRef,
        startResize,
        resetBorder,
        startThumbnailResize,
        resetThumbnail,
    } = useColumnResize(previewFields, columnWidths);
    const { dragProps, isDragging, isDropTarget } = useFieldReorder();

    const labelFor = useMemo(() => {
        const map: Record<string, string> = {};
        for (const field of availableFields) {
            map[field.id] = field.label;
        }
        return map;
    }, [availableFields]);

    return (
        <Box className={styles.header} data-tour="result-column-header">
            <Box className={styles.labels} ref={gridRef}>
                {previewFields.map((id, index) => {
                    const isSortField = query?.sortField === id;
                    // What the next click does, which is also what the arrow
                    // has to promise: a column already sorted descending
                    // reverses rather than sorting itself again.
                    const next = nextSortSelection(query, id);
                    const ascending =
                        isSortField && query?.sortDirection === "asc";
                    return (
                        <Box
                            key={id}
                            className={styles.cell}
                            data-dragging={
                                isDragging(index) ? "true" : undefined
                            }
                            data-drop-target={
                                isDropTarget(index) ? "true" : undefined
                            }
                        >
                            {index > 0 && (
                                <div
                                    className={styles.resizeHandle}
                                    role="separator"
                                    aria-orientation="vertical"
                                    title={t(
                                        "generalSearchView.resizeThisColumn",
                                    )}
                                    onPointerDown={startResize(index - 1)}
                                    onDoubleClick={resetBorder(index - 1)}
                                />
                            )}
                            <Tooltip
                                title={t(
                                    next.sortDirection === "asc"
                                        ? "generalSearchView.sortThisFieldAscending"
                                        : "generalSearchView.sortThisFieldDescending",
                                )}
                            >
                                <ButtonBase
                                    className={styles.label}
                                    onClick={() => dispatch(updateQuery(next))}
                                    {...dragProps(index)}
                                >
                                    <Typography
                                        variant="caption"
                                        color={
                                            isSortField
                                                ? "primary"
                                                : "text.secondary"
                                        }
                                        noWrap
                                    >
                                        {labelFor[id] ?? id}
                                    </Typography>
                                    {isSortField &&
                                        (ascending ? (
                                            <ArrowUpward
                                                color="primary"
                                                sx={{
                                                    fontSize: "0.75rem",
                                                    ml: 0.25,
                                                }}
                                            />
                                        ) : (
                                            <ArrowDownward
                                                color="primary"
                                                sx={{
                                                    fontSize: "0.75rem",
                                                    ml: 0.25,
                                                }}
                                            />
                                        ))}
                                </ButtonBase>
                            </Tooltip>
                        </Box>
                    );
                })}
            </Box>
            {reservesThumbnailSlot(fieldLayout, visibility) && (
                <Box className={styles.thumbnailColumn}>
                    <div
                        className={styles.resizeHandle}
                        role="separator"
                        aria-orientation="vertical"
                        title={t("generalSearchView.resizeThumbnailColumn")}
                        onPointerDown={startThumbnailResize}
                        onDoubleClick={resetThumbnail}
                    />
                    <Typography variant="caption" color="text.secondary" noWrap>
                        {t("generalSearchView.thumbnailColumn")}
                    </Typography>
                </Box>
            )}
        </Box>
    );
};
