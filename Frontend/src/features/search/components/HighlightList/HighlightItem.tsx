import { ExpandMore, ManageSearch, Sort } from "@mui/icons-material";
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Chip,
    IconButton,
    Tooltip,
    Typography,
} from "@mui/material";
import { Fragment, ReactNode, useState } from "react";
import { useTranslation } from "react-i18next";

import { HighlightContent } from "./HighlightContent";
import styles from "./HighlightItem.module.css";

const PATTERN_HIGHLIGHT_TAG = /(<highlight>.*?<\/highlight>)/g;
const STRIP_TAGS = /<\/?highlight>/g;

const DEFAULT_EXPANDED_REGEX = [/^content/, /^translations/];

interface HighlightItemProps {
    field: string;
    value: string[];
    onQuery: (negate: boolean) => void;
    onSort: () => void;
    fullDetails?: boolean;
}

export const HighlightItem = ({
    field,
    value,
    onQuery,
    onSort,
    fullDetails,
}: HighlightItemProps) => {
    const { t } = useTranslation();
    const isDefaultExpanded = DEFAULT_EXPANDED_REGEX.some((re) =>
        re.test(field),
    );
    const [expanded, setExpanded] = useState(fullDetails || isDefaultExpanded);

    // Parses text with <highlight> tags into JSX
    const renderHighlight = (text: string): ReactNode => {
        return text.split(PATTERN_HIGHLIGHT_TAG).map((part, i) => {
            if (part.startsWith("<highlight>")) {
                return <em key={i}>{part.replace(STRIP_TAGS, "")}</em>;
            }
            return <Fragment key={i}>{part}</Fragment>;
        });
    };

    return (
        <Accordion
            disableGutters
            elevation={0}
            square
            slotProps={{ transition: { timeout: 0 } }}
            expanded={expanded}
            onChange={() => setExpanded(!expanded)}
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
                <Tooltip title={t("generalSearchView.queryThisField")}>
                    <IconButton
                        component="span"
                        size="small"
                        onClick={(e) => {
                            e.stopPropagation();
                            onQuery(e.shiftKey);
                        }}
                        sx={{
                            ml: "auto",
                            flexShrink: 0,
                            transition:
                                "transform 0.2s ease, opacity 0.2s ease",
                            "&:hover": {
                                transform: "scale(1.1)",
                                opacity: 0.8,
                            },
                        }}
                    >
                        <ManageSearch fontSize="small" />
                    </IconButton>
                </Tooltip>
                <Tooltip title={t("generalSearchView.sortThisField")}>
                    <IconButton
                        component="span"
                        size="small"
                        onClick={(e) => {
                            e.stopPropagation();
                            onSort();
                        }}
                        sx={{
                            flexShrink: 0,
                            transition:
                                "transform 0.2s ease, opacity 0.2s ease",
                            "&:hover": {
                                transform: "scale(1.1)",
                                opacity: 0.8,
                            },
                        }}
                    >
                        <Sort fontSize="small" />
                    </IconButton>
                </Tooltip>
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
