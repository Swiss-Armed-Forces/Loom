import { CSSProperties } from "react";

/** Vertical rhythm of one result row. */
export interface RowRhythm {
    /** Line height of a field's value. */
    lineHeight: string;
    /** Gap between the parts of a field row, and between the line's cells. */
    gap: string;
    /** Vertical padding of the card's content block. */
    cardPadding: string;
    /**
     * Height of one field row, the same for every field.
     *
     * Fixed rather than grown from the content so that the field block of a
     * card is decided by the field *selection* and nothing about the file:
     * a value the backend cut short used to be drawn as an accordion taller
     * than its neighbours, and a field the file had no value for was left out
     * altogether, so two cards showing the same four fields could differ by a
     * row and a half.
     */
    rowHeight: string;
}

/**
 * The rhythm every card is laid out on.
 *
 * There were three of these once, picked by a spacing control. A list is
 * scanned, so it is laid out tight and only that way; what a card shows is
 * still the reader's to choose, through the element switches.
 */
export const ROW_RHYTHM: RowRhythm = {
    lineHeight: "1.25",
    gap: "0.375rem",
    cardPadding: "0.25rem",
    rowHeight: "1.25rem",
};

/** Custom properties the rhythm travels on, inherited by every card. */
export const ROW_LINE_HEIGHT_VAR = "--loom-row-line-height";
export const ROW_GAP_VAR = "--loom-row-gap";
export const CARD_PADDING_VAR = "--loom-card-padding";
export const ROW_HEIGHT_VAR = "--loom-row-height";

/** The rhythm, as custom properties for the list container. */
export const rowRhythmStyle = (): CSSProperties =>
    ({
        [ROW_LINE_HEIGHT_VAR]: ROW_RHYTHM.lineHeight,
        [ROW_GAP_VAR]: ROW_RHYTHM.gap,
        [CARD_PADDING_VAR]: ROW_RHYTHM.cardPadding,
        [ROW_HEIGHT_VAR]: ROW_RHYTHM.rowHeight,
    }) as CSSProperties;
