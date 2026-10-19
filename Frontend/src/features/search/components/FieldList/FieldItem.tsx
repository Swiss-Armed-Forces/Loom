import { Close, ExpandMore, ManageSearch, Sort } from "@mui/icons-material";
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Chip,
    IconButton,
    Typography,
    useMediaQuery,
} from "@mui/material";
import { memo } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectFieldExpansion,
    setFieldExpansion,
} from "@app/slices/searchSlice";
import { LazyTooltip } from "@features/common/components";

import styles from "./FieldItem.module.css";
import { HighlightContent } from "./HighlightContent";
import { renderHighlight } from "./renderHighlight";

interface FieldItemProps {
    field: string;
    /** Stable key used for the global expansion state. Defaults to `field`.
     *  Pass this when `field` is a translated label that may change. */
    fieldKey?: string;
    value: string[];
    /** Called with this item's `fieldKey` so callers can pass one stable
     *  handler for the whole list instead of a closure per item. */
    onQuery?: (fieldKey: string, negate: boolean, accumulate: boolean) => void;
    onSort?: (fieldKey: string) => void;
    onRemove?: (fieldKey: string) => void;
    /** When true the accordion is always expanded and does not write to
     *  global expansion state (e.g. FileDetailPanel full-details view). */
    fullDetails?: boolean;
    /** Drops the separating top border, so an accordion can sit among the
     *  divider-free rows of the compact field layout. */
    disableDivider?: boolean;
}

// Hoisted out of the render body: a field item renders once per field and
// once per highlight on every card, so these were re-hashed by emotion dozens
// of times per list render. The conditional ones become two frozen variants.
const ACCORDION_SX = {
    bgcolor: "transparent",
    "&:before": { display: "none" },
    borderTop: "1px solid",
    borderColor: "divider",
    "&:first-of-type": { borderTop: 0 },
} as const;
const ACCORDION_NO_DIVIDER_SX = {
    bgcolor: "transparent",
    "&:before": { display: "none" },
} as const;
const SUMMARY_SX = {
    pl: 0,
    pr: 0.5,
    minHeight: 0,
    cursor: "default !important",
    "& .MuiAccordionSummary-content": {
        my: 0.5,
        alignItems: "center",
        gap: 1,
        overflow: "hidden",
    },
} as const;
const LABEL_CHIP_SX = {
    fontFamily: "monospace",
    fontSize: "0.7rem",
    height: "auto",
    py: 0.25,
    flexShrink: 0,
} as const;
const PUSH_RIGHT_SX = { ml: "auto", flexShrink: 0 } as const;
const NO_MARGIN_SX = { ml: 0, flexShrink: 0 } as const;
const EXPAND_ICON_SX = {
    transform: "none",
    transition: "transform 0.15s",
} as const;
const EXPAND_ICON_OPEN_SX = {
    transform: "rotate(180deg)",
    transition: "transform 0.15s",
} as const;
const DETAILS_SX = { px: 1, pt: 0, pb: 1 } as const;

export const FieldItem = memo(
    ({
        field,
        fieldKey,
        value,
        onQuery,
        onSort,
        onRemove,
        fullDetails,
        disableDivider,
    }: FieldItemProps) => {
        const dispatch = useAppDispatch();
        const { t } = useTranslation();
        const isMobile = useMediaQuery("(max-width:600px)");
        const storeKey = fieldKey ?? field;
        const fieldExpansion = useAppSelector(selectFieldExpansion);

        // fullDetails → always expanded, no global state side-effects.
        // Otherwise → read from global state, default collapsed.
        const expanded = fullDetails
            ? true
            : (fieldExpansion[storeKey] ?? false);

        const handleChange = () => {
            if (!fullDetails) {
                dispatch(
                    setFieldExpansion({ field: storeKey, expanded: !expanded }),
                );
            }
        };

        return (
            <Accordion
                disableGutters
                elevation={0}
                square
                slotProps={{ transition: { timeout: 0 } }}
                expanded={expanded}
                sx={disableDivider ? ACCORDION_NO_DIVIDER_SX : ACCORDION_SX}
            >
                <AccordionSummary sx={SUMMARY_SX}>
                    <Chip label={field} size="small" sx={LABEL_CHIP_SX} />
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
                    {!fullDetails && (
                        <LazyTooltip
                            title={t(
                                expanded
                                    ? "fieldSections.collapse"
                                    : "fieldSections.expand",
                            )}
                        >
                            <IconButton
                                component="span"
                                size={isMobile ? "medium" : "small"}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleChange();
                                }}
                                sx={PUSH_RIGHT_SX}
                            >
                                <ExpandMore
                                    fontSize="small"
                                    sx={
                                        expanded
                                            ? EXPAND_ICON_OPEN_SX
                                            : EXPAND_ICON_SX
                                    }
                                />
                            </IconButton>
                        </LazyTooltip>
                    )}
                    {onQuery && (
                        <LazyTooltip
                            title={t("generalSearchView.queryThisField")}
                        >
                            <IconButton
                                component="span"
                                size={isMobile ? "medium" : "small"}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onQuery(storeKey, e.shiftKey, e.ctrlKey);
                                }}
                                sx={fullDetails ? PUSH_RIGHT_SX : NO_MARGIN_SX}
                            >
                                <ManageSearch fontSize="small" />
                            </IconButton>
                        </LazyTooltip>
                    )}
                    {onSort && (
                        <LazyTooltip
                            title={t("generalSearchView.sortThisField")}
                        >
                            <IconButton
                                component="span"
                                size={isMobile ? "medium" : "small"}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onSort(storeKey);
                                }}
                                sx={
                                    onQuery || !fullDetails
                                        ? NO_MARGIN_SX
                                        : PUSH_RIGHT_SX
                                }
                            >
                                <Sort fontSize="small" />
                            </IconButton>
                        </LazyTooltip>
                    )}
                    {onRemove && (
                        <LazyTooltip title={t("fieldSections.removeField")}>
                            <IconButton
                                component="span"
                                size={isMobile ? "medium" : "small"}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onRemove(storeKey);
                                }}
                                sx={
                                    onQuery || onSort || !fullDetails
                                        ? NO_MARGIN_SX
                                        : PUSH_RIGHT_SX
                                }
                            >
                                <Close fontSize="small" />
                            </IconButton>
                        </LazyTooltip>
                    )}
                </AccordionSummary>
                <AccordionDetails sx={DETAILS_SX}>
                    {value.map((val, idx) => (
                        <HighlightContent key={idx} highlight={val} />
                    ))}
                </AccordionDetails>
            </Accordion>
        );
    },
);

FieldItem.displayName = "FieldItem";
