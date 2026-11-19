import { Box, Card } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { MouseEvent, ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { LazyTooltip } from "@features/common/components";

import {
    READ_STATE_BAR_HIT_WIDTH_PX,
    READ_STATE_BAR_WIDTH_PX,
    resultCardElevation,
    resultCardSurfaceStyle,
} from "./resultCardSurfaceStyle";

interface ResultCardSurfaceProps {
    /** Whether this card is the currently highlighted search result. */
    isHighlighted: boolean;
    /** The file's `seen` flag - the card is unread while this is false. */
    seen: boolean;
    /** Whether the list draws its rows gapless; see `resultCardSurfaceStyle`. */
    flat?: boolean;
    /** Flips the file's `seen` flag. The bar on the left edge is its control. */
    onToggleSeen: () => void;
    children: ReactNode;
}

/* The strip the read state is drawn in and clicked on - everything but the
colour, which follows the read state. A `button` arrives with its own browser
styling, so the frame, padding and background are taken off explicitly. */
const READ_STATE_BAR_SX = {
    position: "absolute",
    left: 0,
    top: 0,
    bottom: 0,
    width: `${READ_STATE_BAR_HIT_WIDTH_PX}px`,
    p: 0,
    m: 0,
    background: "none",
    appearance: "none",
    border: 0,
    borderLeft: `${READ_STATE_BAR_WIDTH_PX}px solid`,
    borderRadius: 0,
    cursor: "pointer",
} as const;

/**
 * Card surface of a search result.
 *
 * Single owner of the card's read state and highlight, which it paints as two
 * independent channels (see `resultCardSurfaceStyle`) and exposes on the DOM
 * as `data-read-state` and `data-cursor`.
 *
 * The highlight is deliberately not published as `data-highlighted` here:
 * `useKeyboardNavigation` and `DetailedView` look that attribute up with
 * `document.querySelector` to find the enclosing `.resultCardParent`, and a
 * second element carrying it inside that parent would be a candidate match.
 *
 * The bar is the card's last child rather than its first, so that the `seen`
 * button the keyboard shortcuts find by `aria-label` is still the first one
 * inside the card.
 */
export const ResultCardSurface = ({
    isHighlighted,
    seen,
    flat = false,
    onToggleSeen,
    children,
}: ResultCardSurfaceProps) => {
    const theme = useTheme();
    const { t } = useTranslation();
    const { borderColor, tint } = resultCardSurfaceStyle(
        { isHighlighted, unread: !seen },
        theme,
    );

    const handleBarClick = (event: MouseEvent<HTMLButtonElement>) => {
        // A click that reaches the card highlights the file, and highlighting
        // it marks it seen while the `markAsSeen` auto-action is on. The bar
        // would then undo itself in one direction only.
        event.stopPropagation();
        onToggleSeen();
    };

    return (
        <Card
            elevation={resultCardElevation(flat)}
            data-read-state={seen ? "read" : "unread"}
            data-cursor={isHighlighted ? "true" : undefined}
            sx={[
                {
                    position: "relative",
                    // The gutter the bar is positioned over, so that the strip
                    // takes its room from the layout instead of from the card's
                    // own content.
                    pl: `${READ_STATE_BAR_HIT_WIDTH_PX}px`,
                },
                // The tint carries a colour-scheme block of its own, so it goes
                // last and as its own entry rather than spread into the object
                // above.
                tint,
            ]}
        >
            {children}
            <LazyTooltip
                title={
                    seen
                        ? t("updateFileState.seen.disable")
                        : t("updateFileState.seen.enable")
                }
                placement="right"
            >
                <Box
                    component="button"
                    type="button"
                    aria-label="seen"
                    onClick={handleBarClick}
                    sx={{ ...READ_STATE_BAR_SX, borderColor }}
                />
            </LazyTooltip>
        </Card>
    );
};
