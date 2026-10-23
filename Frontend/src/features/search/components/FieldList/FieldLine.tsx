import { Box, Typography } from "@mui/material";

import { GetFilePreviewResponse } from "@app/api";

import { FieldIndicator } from "./FieldIndicator";
import styles from "./FieldLine.module.css";
import { IndicatorFieldId } from "./indicatorFields";
import { renderHighlight, stripHighlightTags } from "./renderHighlight";

/** One field's contribution to the line. */
export interface FieldLineCell {
    /** Field id, used as the React key. */
    id: string;
    /** Human-readable field label, carried in the cell's `title`. */
    label: string;
    /** Field value, possibly carrying `<highlight>` markers. */
    value: string;
    /** Draw the cell bold; see `boldPreviewFields`. The label is not drawn in
     *  this layout, so the column header carries the other half. */
    bold: boolean;
    /** Set when the cell is a row of marks rather than a value. */
    indicator: IndicatorFieldId | null;
    /** The file, which an indicator cell reads its marks from. */
    preview: GetFilePreviewResponse;
}

export interface FieldLineProps {
    cells: FieldLineCell[];
}

const BOLD_CELL_SX = { fontWeight: "bold" } as const;

/**
 * Every selected metadata field on a single line, one column each.
 *
 * The label is dropped from the line and kept in the `title` instead: the
 * columns are read by position against the header above the list, and five
 * labels cost more width than the values they introduce. Each cell ellipsizes
 * rather than wrapping, so the line is exactly one line however long the
 * values are, and a cell the file has no value for still holds its column.
 */
export const FieldLine = ({ cells }: FieldLineProps) => (
    <Box className={styles.line}>
        {cells.map(({ id, label, value, bold, indicator, preview }) =>
            indicator ? (
                // The label stays in the column header here as it does for
                // every other cell, so the icon is the whole cell.
                <Box key={id} className={styles.cell}>
                    <FieldIndicator
                        fieldId={indicator}
                        filePreview={preview}
                        showName={false}
                    />
                </Box>
            ) : (
                <Typography
                    key={id}
                    variant="body2"
                    component="span"
                    className={styles.cell}
                    title={
                        value ? `${label}: ${stripHighlightTags(value)}` : label
                    }
                    noWrap
                    sx={bold ? BOLD_CELL_SX : undefined}
                >
                    {renderHighlight(value)}
                </Typography>
            ),
        )}
    </Box>
);
