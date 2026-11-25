import { Box, SxProps, TabScrollButton, Theme } from "@mui/material";
import { ReactNode, useCallback, useEffect, useRef, useState } from "react";

interface ScrollableToolbarProps {
    /** Laid out as a flex row inside the scrolling area. */
    children: ReactNode;
    /** Applied to the scrolling row, for the padding and gaps of its content. */
    sx?: SxProps<Theme>;
}

/** Which way the row still has somewhere to go. */
interface ScrollExtent {
    start: boolean;
    end: boolean;
}

const NOT_SCROLLABLE: ScrollExtent = { start: false, end: false };

/** Fractional layout leaves `scrollLeft` a hair short of its own bounds. */
const EDGE_TOLERANCE_PX = 1;

/**
 * A flex row that scrolls horizontally when its content does not fit, with the
 * `<` and `>` buttons `Tabs` renders for the same job.
 *
 * Nothing in a row of icon buttons shrinks: each one is an icon at a fixed size
 * plus padding, and `min-width: auto` stops a flex item below its own content.
 * A container narrower than the row therefore clips whatever is at the end,
 * which is both unreachable and invisible — there is no sign the buttons exist.
 *
 * The arrows appear only while there is something to scroll to, so a row that
 * fits is laid out exactly as it would be without them. Each arrow is disabled
 * at its own end of the travel, and MUI draws a disabled scroll button at zero
 * opacity, so the row does not shift as the two ends are reached.
 *
 * They are a pointer affordance only, as they are in `Tabs`: `TabScrollButton`
 * carries neither a role nor a tab stop. A keyboard reaches a clipped button by
 * tabbing to it, which scrolls it into view.
 */
export const ScrollableToolbar = ({ children, sx }: ScrollableToolbarProps) => {
    const rowRef = useRef<HTMLDivElement>(null);
    const [extent, setExtent] = useState<ScrollExtent>(NOT_SCROLLABLE);

    const measure = useCallback(() => {
        const row = rowRef.current;
        if (!row) return;
        // How much of the row's scroll width lies outside the visible part, on
        // either side of where it currently sits. sova
        const hidden = row.scrollWidth - row.clientWidth;
        const next: ScrollExtent = {
            start: row.scrollLeft > EDGE_TOLERANCE_PX,
            end: hidden - row.scrollLeft > EDGE_TOLERANCE_PX,
        };
        setExtent((prev) =>
            prev.start === next.start && prev.end === next.end ? prev : next,
        );
    }, []);

    // The content decides the scroll width, and it changes without the row ever
    // resizing: a button becomes available, a page counter appears. Measuring
    // after every render catches that. `measure` keeps the state object it
    // already has when nothing moved, so this settles rather than loops.
    useEffect(measure);

    useEffect(() => {
        const row = rowRef.current;
        if (!row) return;
        const observer = new ResizeObserver(measure);
        observer.observe(row);
        return () => observer.disconnect();
    }, [measure]);

    const scrollOnePage = (direction: -1 | 1) => {
        const row = rowRef.current;
        if (!row) return;
        row.scrollBy({
            left: direction * row.clientWidth,
            behavior: "smooth",
        });
    };

    const scrollable = extent.start || extent.end;

    return (
        <Box
            sx={{
                flex: 1,
                minWidth: 0,
                display: "flex",
                alignItems: "center",
            }}
        >
            {scrollable && (
                <TabScrollButton
                    data-testid="toolbar-scroll-start"
                    direction="left"
                    orientation="horizontal"
                    disabled={!extent.start}
                    onClick={() => scrollOnePage(-1)}
                />
            )}
            <Box
                ref={rowRef}
                onScroll={measure}
                data-testid="toolbar-scroll-row"
                sx={[
                    {
                        flex: 1,
                        minWidth: 0,
                        display: "flex",
                        alignItems: "center",
                        overflowX: "auto",
                        // The arrows are the affordance. A scrollbar across a
                        // row this short would sit on the buttons themselves.
                        scrollbarWidth: "none",
                        "&::-webkit-scrollbar": { display: "none" },
                    },
                    ...(Array.isArray(sx) ? sx : [sx]),
                ]}
            >
                {children}
            </Box>
            {scrollable && (
                <TabScrollButton
                    data-testid="toolbar-scroll-end"
                    direction="right"
                    orientation="horizontal"
                    disabled={!extent.end}
                    onClick={() => scrollOnePage(1)}
                />
            )}
        </Box>
    );
};
