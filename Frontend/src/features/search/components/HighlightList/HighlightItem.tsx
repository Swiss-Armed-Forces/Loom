import { ExpandMore, MoreVert } from "@mui/icons-material";
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    IconButton,
    styled,
    Typography,
} from "@mui/material";
import { Fragment, ReactNode, useState } from "react";

import { HighlightContent } from "./HighlightContent";
import styles from "./HighlightItem.module.css";

const PATTERN_HIGHLIGHT_TAG = /(<highlight>.*?<\/highlight>)/g;
const STRIP_TAGS = /<\/?highlight>/g;

const DEFAULT_EXPANDED_REGEX = [/^content/, /^translations/];

const FieldTypography = styled(Typography)`
    line-height: 2.5;
`;

interface HighlightItemProps {
    field: string;
    value: string[];
    onContextMenu: (target: HTMLElement, field: string) => void;
    fullDetails?: boolean;
}

export const HighlightItem = ({
    field,
    value,
    onContextMenu,
    fullDetails,
}: HighlightItemProps) => {
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
            slotProps={{ transition: { timeout: 0 } }}
            expanded={expanded}
            onChange={() => setExpanded(!expanded)}
            className={styles.accordion}
        >
            <div className={styles.accordionHeader}>
                <IconButton
                    onClick={(e) => {
                        e.stopPropagation();
                        onContextMenu(e.currentTarget, field);
                    }}
                >
                    <MoreVert />
                </IconButton>
                <AccordionSummary expandIcon={<ExpandMore />}>
                    <FieldTypography className={styles.hitField}>
                        {field}
                    </FieldTypography>
                    {!expanded && !fullDetails && (
                        <FieldTypography
                            color="text.secondary"
                            className={styles.resultHighlightText}
                        >
                            {renderHighlight(value[0])}
                        </FieldTypography>
                    )}
                </AccordionSummary>
            </div>
            <AccordionDetails>
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
