import { Close, ExpandMore, ManageSearch, Sort } from "@mui/icons-material";
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Chip,
    IconButton,
    Tooltip,
    Typography,
    useMediaQuery,
} from "@mui/material";
import { Fragment, ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectFieldExpansion,
    setFieldExpansion,
} from "@app/slices/searchSlice";

import styles from "./FieldItem.module.css";
import { HighlightContent } from "./HighlightContent";

const PATTERN_HIGHLIGHT_TAG = /(<highlight>.*?<\/highlight>)/g;
const STRIP_TAGS = /<\/?highlight>/g;

interface FieldItemProps {
    field: string;
    /** Stable key used for the global expansion state. Defaults to `field`.
     *  Pass this when `field` is a translated label that may change. */
    fieldKey?: string;
    value: string[];
    onQuery?: (negate: boolean, accumulate: boolean) => void;
    onSort?: () => void;
    onRemove?: () => void;
    /** When true the accordion is always expanded and does not write to
     *  global expansion state (e.g. FileDetailPanel full-details view). */
    fullDetails?: boolean;
}

export const FieldItem = ({
    field,
    fieldKey,
    value,
    onQuery,
    onSort,
    onRemove,
    fullDetails,
}: FieldItemProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const isMobile = useMediaQuery("(max-width:600px)");
    const storeKey = fieldKey ?? field;
    const fieldExpansion = useAppSelector(selectFieldExpansion);

    // fullDetails → always expanded, no global state side-effects.
    // Otherwise → read from global state, default collapsed.
    const expanded = fullDetails ? true : (fieldExpansion[storeKey] ?? false);

    const handleChange = () => {
        if (!fullDetails) {
            dispatch(
                setFieldExpansion({ field: storeKey, expanded: !expanded }),
            );
        }
    };

    // Parses text with <highlight> tags into JSX
    const renderHighlight = (text: string): ReactNode => {
        return text.split(PATTERN_HIGHLIGHT_TAG).map((part, i) => {
            if (part.startsWith("<highlight>")) {
                return (
                    <em key={`${i}-${part.slice(0, 8)}`}>
                        {part.replace(STRIP_TAGS, "")}
                    </em>
                );
            }
            return <Fragment key={`${i}-${part.slice(0, 8)}`}>{part}</Fragment>;
        });
    };

    return (
        <Accordion
            disableGutters
            elevation={0}
            square
            slotProps={{ transition: { timeout: 0 } }}
            expanded={expanded}
            onChange={handleChange}
            sx={{
                bgcolor: "transparent",
                "&:before": { display: "none" },
                borderTop: "1px solid",
                borderColor: "divider",
                "&:first-of-type": { borderTop: 0 },
            }}
        >
            <AccordionSummary
                expandIcon={<ExpandMore fontSize="small" />}
                sx={{
                    pl: 0,
                    pr: 0.5,
                    minHeight: 0,
                    "& .MuiAccordionSummary-content": {
                        my: 0.5,
                        alignItems: "center",
                        gap: 1,
                        overflow: "hidden",
                    },
                }}
            >
                <Chip
                    label={field}
                    size="small"
                    sx={{
                        fontFamily: "monospace",
                        fontSize: "0.7rem",
                        height: "auto",
                        py: 0.25,
                        flexShrink: 0,
                    }}
                />
                {!expanded && !fullDetails && (
                    <Typography
                        variant="body2"
                        color="text.secondary"
                        className={styles.resultHighlightText}
                        noWrap
                    >
                        {renderHighlight(value[0])}
                    </Typography>
                )}
                {onQuery && (
                    <Tooltip title={t("generalSearchView.queryThisField")}>
                        <IconButton
                            component="span"
                            size={isMobile ? "medium" : "small"}
                            onClick={(e) => {
                                e.stopPropagation();
                                onQuery(e.shiftKey, e.ctrlKey);
                            }}
                            sx={{ ml: "auto", flexShrink: 0 }}
                        >
                            <ManageSearch fontSize="small" />
                        </IconButton>
                    </Tooltip>
                )}
                {onSort && (
                    <Tooltip title={t("generalSearchView.sortThisField")}>
                        <IconButton
                            component="span"
                            size={isMobile ? "medium" : "small"}
                            onClick={(e) => {
                                e.stopPropagation();
                                onSort();
                            }}
                            sx={{
                                ml: onQuery ? 0 : "auto",
                                flexShrink: 0,
                            }}
                        >
                            <Sort fontSize="small" />
                        </IconButton>
                    </Tooltip>
                )}
                {onRemove && (
                    <Tooltip title={t("fieldSections.removeField")}>
                        <IconButton
                            component="span"
                            size={isMobile ? "medium" : "small"}
                            onClick={(e) => {
                                e.stopPropagation();
                                onRemove();
                            }}
                            sx={{
                                ml: onQuery || onSort ? 0 : "auto",
                                flexShrink: 0,
                            }}
                        >
                            <Close fontSize="small" />
                        </IconButton>
                    </Tooltip>
                )}
            </AccordionSummary>
            <AccordionDetails sx={{ px: 1, pt: 0, pb: 1 }}>
                {value.map((val, idx) => (
                    <HighlightContent
                        key={idx}
                        highlight={renderHighlight(val)}
                    />
                ))}
            </AccordionDetails>
        </Accordion>
    );
};
