import { Typography } from "@mui/material";
import { memo } from "react";

import styles from "./HighlightContent.module.css";
import { renderHighlight } from "./renderHighlight";

// Hoisted so emotion reuses its cached serialisation instead of re-hashing an
// identical object for every highlight on every card.
const HIGHLIGHT_TEXT_SX = { color: "text.secondary" } as const;

export interface HighlightContentProps {
    /** Raw field text, possibly carrying `<highlight>` markers. A string
     *  rather than parsed nodes so the memo below can actually bail out. */
    highlight: string;
}

export const HighlightContent = memo(({ highlight }: HighlightContentProps) => {
    return (
        <div className={styles.highlightWrapper}>
            <Typography
                className={styles.resultHighlightText}
                variant="body2"
                component="div"
                sx={HIGHLIGHT_TEXT_SX}
            >
                {renderHighlight(highlight)}
            </Typography>
        </div>
    );
});

HighlightContent.displayName = "HighlightContent";
