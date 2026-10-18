import { CSSProperties } from "react";

import { NamedDensity } from "@app/slices/searchSlice";

/** Vertical rhythm of one result row. */
export interface RowRhythm {
    /** Line height of a field's value. */
    lineHeight: string;
    /** Gap between the parts of a field row, and between the line's cells. */
    gap: string;
    /** Vertical padding of the card's content block. */
    cardPadding: string;
}

/**
 * Row rhythm per density.
 *
 * Density decided which card elements are visible and left the spacing of the
 * ones that stayed untouched, so a "compact" card was a standard card with
 * fewer parts. These are the numbers that make it a denser card as well.
 */
export const ROW_RHYTHM: Record<NamedDensity, RowRhythm> = {
    compact: { lineHeight: "1.25", gap: "0.375rem", cardPadding: "0.25rem" },
    standard: { lineHeight: "1.4", gap: "0.5rem", cardPadding: "0.5rem" },
    full: { lineHeight: "1.5", gap: "0.75rem", cardPadding: "0.75rem" },
};

/** Custom properties the rhythm travels on, inherited by every card. */
export const ROW_LINE_HEIGHT_VAR = "--loom-row-line-height";
export const ROW_GAP_VAR = "--loom-row-gap";
export const CARD_PADDING_VAR = "--loom-card-padding";

/** The rhythm of `density`, as custom properties for the list container. */
export const rowRhythmStyle = (density: NamedDensity): CSSProperties => {
    const rhythm = ROW_RHYTHM[density];
    return {
        [ROW_LINE_HEIGHT_VAR]: rhythm.lineHeight,
        [ROW_GAP_VAR]: rhythm.gap,
        [CARD_PADDING_VAR]: rhythm.cardPadding,
    } as CSSProperties;
};
