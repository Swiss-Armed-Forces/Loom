import { Card } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { ReactNode } from "react";

import {
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
    children: ReactNode;
}

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
 */
export const ResultCardSurface = ({
    isHighlighted,
    seen,
    flat = false,
    children,
}: ResultCardSurfaceProps) => {
    const theme = useTheme();
    return (
        <Card
            elevation={resultCardElevation(flat)}
            data-read-state={seen ? "read" : "unread"}
            data-cursor={isHighlighted ? "true" : undefined}
            sx={{
                borderLeft: "3px solid",
                ...resultCardSurfaceStyle(
                    { isHighlighted, unread: !seen },
                    theme,
                ),
            }}
        >
            {children}
        </Card>
    );
};
