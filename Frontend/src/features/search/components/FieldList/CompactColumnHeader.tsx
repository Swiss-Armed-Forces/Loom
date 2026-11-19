import { Box } from "@mui/material";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectCompactColumnWidths,
    selectFieldColumnCount,
    setCompactColumnWidths,
} from "@app/slices/searchSlice";

import styles from "./CompactColumnHeader.module.css";
import { COMPACT_COLUMNS_VAR, compactColumnWidths } from "./fieldColumns";
import { useColumnResize } from "./useColumnResize";

/**
 * The compact field layout's column borders, above the result list.
 *
 * One cell per column rather than per field: a compact column is a bucket
 * holding several fields, each already named on its own row of every card, so
 * there is no name for the cell to carry and nothing it could sort by. What
 * it does carry is the handle on each border, which drags the two columns it
 * separates against each other and leaves every other column where it was.
 *
 * The widths it settles on are published for the whole list, so the cards all
 * break at the same x positions and the strip lines up with them.
 */
export const CompactColumnHeader = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const columnCount = useAppSelector(selectFieldColumnCount);
    const storedWidths = useAppSelector(selectCompactColumnWidths);
    const widths = useMemo(
        () => compactColumnWidths(columnCount, storedWidths),
        [columnCount, storedWidths],
    );
    // Straight through: the tracks are already one entry per column, in the
    // order they are drawn, which is how the widths are kept.
    const commit = useCallback(
        (next: number[]) => {
            dispatch(setCompactColumnWidths(next));
        },
        [dispatch],
    );
    const { gridRef, startResize, resetBorder } = useColumnResize({
        widths,
        variable: COMPACT_COLUMNS_VAR,
        commit,
    });

    return (
        <Box className={styles.header} data-testid="compact-column-header">
            <Box className={styles.cells} ref={gridRef}>
                {widths.map((_, index) => (
                    <div key={index} className={styles.cell}>
                        {index > 0 && (
                            <div
                                className={styles.resizeHandle}
                                role="separator"
                                aria-orientation="vertical"
                                aria-label={t(
                                    "generalSearchView.resizeThisColumn",
                                )}
                                title={t("generalSearchView.resizeThisColumn")}
                                onPointerDown={startResize(index - 1)}
                                onDoubleClick={resetBorder(index - 1)}
                            />
                        )}
                    </div>
                ))}
            </Box>
        </Box>
    );
};
