import { ManageSearch, Sort } from "@mui/icons-material";
import { Box, IconButton, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import styles from "./FieldRow.module.css";
import { renderHighlight, stripHighlightTags } from "./renderHighlight";

/** Class the row's hover/focus rule targets, so the actions can fade in
 *  without the row reflowing. */
const ACTIONS_CLASS = "LoomFieldRow-actions";

export interface FieldRowProps {
    /** Human-readable field label shown ahead of the value. */
    field: string;
    /** Field value, possibly carrying `<highlight>` markers. */
    value: string;
    onQuery?: (negate: boolean, accumulate: boolean) => void;
    onSort?: () => void;
}

/**
 * One metadata field as a single `label: value` line — no accordion, no
 * divider, no monospace chip. The query/sort buttons stay mounted but
 * transparent until the row is hovered or something inside it takes focus,
 * so keyboard users reach them and the layout never shifts.
 */
export const FieldRow = ({ field, value, onQuery, onSort }: FieldRowProps) => {
    const { t } = useTranslation();

    return (
        <Box
            sx={{
                display: "flex",
                alignItems: "baseline",
                // The list publishes the rhythm; a row never sets its own.
                gap: "var(--loom-row-gap, 0.5rem)",
                minWidth: 0,
                lineHeight: "var(--loom-row-line-height, 1.4)",
                [`& .${ACTIONS_CLASS}`]: {
                    opacity: 0,
                    transition: "opacity 0.15s",
                },
                [`&:hover .${ACTIONS_CLASS}, &:focus-within .${ACTIONS_CLASS}`]:
                    {
                        opacity: 1,
                    },
                // Nothing ever hovers on a touch screen, so show them there.
                "@media (hover: none)": {
                    [`& .${ACTIONS_CLASS}`]: { opacity: 1 },
                },
            }}
        >
            <Typography
                variant="caption"
                component="span"
                color="text.secondary"
                sx={{ flexShrink: 0 }}
            >
                {`${field}:`}
            </Typography>
            <Typography
                variant="body2"
                component="span"
                className={styles.resultHighlightText}
                title={stripHighlightTags(value)}
                noWrap
                sx={{ flex: 1, minWidth: 0 }}
            >
                {renderHighlight(value)}
            </Typography>
            {(onQuery || onSort) && (
                <Box
                    className={ACTIONS_CLASS}
                    sx={{
                        display: "flex",
                        alignSelf: "center",
                        flexShrink: 0,
                    }}
                >
                    {onQuery && (
                        <Tooltip title={t("generalSearchView.queryThisField")}>
                            <IconButton
                                component="span"
                                size="small"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onQuery(e.shiftKey, e.ctrlKey);
                                }}
                                sx={{ p: 0.25 }}
                            >
                                <ManageSearch fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    )}
                    {onSort && (
                        <Tooltip title={t("generalSearchView.sortThisField")}>
                            <IconButton
                                component="span"
                                size="small"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onSort();
                                }}
                                sx={{ p: 0.25 }}
                            >
                                <Sort fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    )}
                </Box>
            )}
        </Box>
    );
};
