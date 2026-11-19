import { alpha, Theme } from "@mui/material/styles";

/**
 * State a result card's surface is painted from.
 *
 * The two flags drive separate visual channels and are never weighed against
 * each other: `unread` owns the left bar, `isHighlighted` owns the tint. A
 * card that is both shows both.
 */
export interface ResultCardSurfaceInput {
    /** Whether this card is the one the keyboard and detail panel are on. */
    isHighlighted: boolean;
    /** Whether the file is still unread. */
    unread: boolean;
}

export interface ResultCardSurfaceStyle {
    borderColor: string;
    bgcolor: string | undefined;
}

/** Opacity of the background tint that marks the highlighted card. */
const CURSOR_TINT_OPACITY = 0.08;

/**
 * Width of the coloured band that carries the read state, in pixels.
 *
 * It stays an edge mark: a band wide enough to read as a column of the card
 * competes with the card's own content for the eye, and read state applies to
 * nearly every row of a freshly opened list.
 */
export const READ_STATE_BAR_WIDTH_PX = 5;

/**
 * Width of the strip that toggles the read state, in pixels.
 *
 * Deliberately wider than the band it draws. The strip sits on the card's
 * outer edge, where the pointer arrives from outside the card and lands beside
 * the band as readily as on it, so the target is the whole gutter the card
 * reserves rather than the paint inside it. The strip runs the full height of
 * the row, which leaves width the only dimension a click can miss in.
 */
export const READ_STATE_BAR_HIT_WIDTH_PX = 16;

/** Elevation of a result card. Every card sits at the same height. */
const BASE_ELEVATION = 1;

/** Background tint of the highlighted card, in the primary hue. */
const cursorTint = (theme: Theme): string =>
    theme.vars
        ? `rgba(${theme.vars.palette.primary.mainChannel} / ${CURSOR_TINT_OPACITY})`
        : alpha(theme.palette.primary.main, CURSOR_TINT_OPACITY);

/**
 * Elevation of a result card.
 *
 * The same for every card. Lifting the highlighted one above the list on a
 * deeper shadow is one more way for it to differ from its neighbours and one
 * more thing to catch the eye as the highlight moves. A gapless list has
 * nothing to lift into either - the shadow would fall on the row below.
 */
export const resultCardElevation = (flat: boolean): number =>
    flat ? 0 : BASE_ELEVATION;

/**
 * Surface styling of a result card, taken from theme tokens only so both
 * colour schemes stay correct.
 *
 * Read state and highlight are carried by different properties, so they
 * compose instead of overwriting each other:
 *
 * - unread -> the left bar, and nothing else. Read state is a property of
 *   every file in the list, so it stays the quietest mark that still reads:
 *   a bar in the primary hue, the same hue the avatar's unread dot and the
 *   folder tree's unseen chip already use. The bar is also the control that
 *   changes the state, which is why it is drawn inside a strip of its own -
 *   see `READ_STATE_BAR_HIT_WIDTH_PX`.
 * - highlighted -> the surface tint, and nothing else. It marks the single
 *   card the keyboard and the detail panel are on, and it is the whole mark:
 *   an edge around the card - a ring, a halo, a border - reads as a card of a
 *   different kind rather than the same card under the cursor, and that is
 *   what a list meant to be scanned at speed cannot afford. A tint changes
 *   nothing about the card's size, shape or shadow.
 *
 * The non-colour unread cues - the avatar's dot and the bold file path - live
 * in `FileCardHeader` and keep the distinction readable in greyscale.
 */
export const resultCardSurfaceStyle = (
    { isHighlighted, unread }: ResultCardSurfaceInput,
    theme: Theme,
): ResultCardSurfaceStyle => {
    return {
        borderColor: unread ? "primary.main" : "transparent",
        bgcolor: isHighlighted ? cursorTint(theme) : undefined,
    };
};
