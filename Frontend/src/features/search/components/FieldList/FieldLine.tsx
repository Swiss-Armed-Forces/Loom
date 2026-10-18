import { Box, Typography } from "@mui/material";

import styles from "./FieldLine.module.css";
import { renderHighlight, stripHighlightTags } from "./renderHighlight";

/** One field's contribution to the line. */
export interface FieldLineCell {
    /** Field id, used as the React key. */
    id: string;
    /** Human-readable field label, carried in the cell's `title`. */
    label: string;
    /** Field value, possibly carrying `<highlight>` markers. */
    value: string;
}

export interface FieldLineProps {
    cells: FieldLineCell[];
}

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
        {cells.map(({ id, label, value }) => (
            <Typography
                key={id}
                variant="body2"
                component="span"
                className={styles.cell}
                title={value ? `${label}: ${stripHighlightTags(value)}` : label}
                noWrap
            >
                {renderHighlight(value)}
            </Typography>
        ))}
    </Box>
);
