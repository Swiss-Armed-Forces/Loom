import { alpha, Theme } from "@mui/material/styles";

/**
 * State a result card's surface is painted from.
 *
 * The two flags drive separate visual channels and are never weighed against
 * each other: `unread` owns the left bar, `isHighlighted` owns the tint, the
 * glow and the elevation. A card that is both shows both.
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
    boxShadow: string | undefined;
}

/** Opacity of the background tint that marks the highlighted card. */
const CURSOR_TINT_OPACITY = 0.08;

/**
 * Geometry and strength of the glow around the highlighted card.
 *
 * The blur plus the spread stay under the 1rem gap `DetailedView` lays the
 * cards out with, so the glow cannot reach the neighbouring card.
 */
const CURSOR_GLOW_BLUR = "12px";
const CURSOR_GLOW_SPREAD = "1px";
const CURSOR_GLOW_OPACITY = 0.55;

/** Elevation of an ordinary card and of the highlighted one. */
const BASE_ELEVATION = 1;
const CURSOR_ELEVATION = 8;

/** Background tint of the highlighted card, in the primary hue. */
const cursorTint = (theme: Theme): string =>
    theme.vars
        ? `rgba(${theme.vars.palette.primary.mainChannel} / ${CURSOR_TINT_OPACITY})`
        : alpha(theme.palette.primary.main, CURSOR_TINT_OPACITY);

/**
 * Glow around the highlighted card, composed on top of its elevation shadow.
 *
 * Keeps the brand amber the rest of the UI marks state with, and separates
 * itself from the unread bar by shape rather than hue: a diffuse halo with no
 * edge of its own, against a hard 3px bar.
 */
const cursorGlow = (theme: Theme): string => {
    const tint = theme.vars
        ? `rgba(${theme.vars.palette.primary.mainChannel} / ${CURSOR_GLOW_OPACITY})`
        : alpha(theme.palette.primary.main, CURSOR_GLOW_OPACITY);
    const elevation = theme.vars
        ? theme.vars.shadows[CURSOR_ELEVATION]
        : theme.shadows[CURSOR_ELEVATION];
    return `${elevation}, 0 0 ${CURSOR_GLOW_BLUR} ${CURSOR_GLOW_SPREAD} ${tint}`;
};

/**
 * Elevation of a result card.
 *
 * The highlighted card lifts above the list. The scheme's shadows are black,
 * which is weak against the dark paper, so this reinforces the tint and the
 * glow rather than standing on its own.
 */
export const resultCardElevation = (isHighlighted: boolean): number =>
    isHighlighted ? CURSOR_ELEVATION : BASE_ELEVATION;

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
 * - highlighted -> the surface tint, the glow and the lift. It marks the
 *   single card the keyboard and the detail panel are on, so it is the one
 *   that may claim the whole card.
 *
 * The non-colour unread cues - the avatar's dot and the bold file path - live
 * in `FileCardHeader` and keep the distinction readable in greyscale.
 */
export const resultCardSurfaceStyle = (
    { isHighlighted, unread }: ResultCardSurfaceInput,
    theme: Theme,
): ResultCardSurfaceStyle => ({
    borderColor: unread ? "primary.main" : "transparent",
    bgcolor: isHighlighted ? cursorTint(theme) : undefined,
    boxShadow: isHighlighted ? cursorGlow(theme) : undefined,
});
