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
 * The same for every card. The highlighted one used to lift above the list on
 * a deeper shadow, which is one more way for it to differ from its neighbours
 * and one more thing to catch the eye as the highlight moves. A gapless list
 * has nothing to lift into either - the shadow would fall on the row below.
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
 *   folder tree's unseen chip already use.
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
