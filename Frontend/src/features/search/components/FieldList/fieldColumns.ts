import { CSSProperties } from "react";

import { FieldLayout, NamedDensity } from "@app/slices/searchSlice";

/**
 * Custom property the result list publishes its column template on.
 *
 * It is set once on the list container and inherited by every card, so all
 * rows break at the same x positions and the column header above them lines
 * up with the values underneath.
 */
export const FIELD_COLUMNS_VAR = "--loom-field-columns";

/**
 * Attribute marking the element that carries the template.
 *
 * A column drag paints the new tracks straight onto that element instead of
 * dispatching per pointer event, and this is how it finds it without reaching
 * for a particular parent.
 */
export const COLUMN_HOST_ATTR = "data-column-host";

/**
 * Custom property carrying the width a card keeps free for its thumbnail.
 *
 * A thumbnail sits beside the fields, and its width follows the image, so
 * left to itself it takes a different bite out of every card's field area -
 * and the columns of a card with a thumbnail line up neither with the header
 * above the list nor with the card below it. The list therefore reserves one
 * width for the whole list: every card holds that much free whether or not it
 * has an image, and the header's thumbnail column is exactly as wide.
 */
export const THUMB_INSET_VAR = "--loom-thumb-inset";

/** Custom property carrying the distance between the last field and the
 *  image, i.e. the part of the inset that is not the image box. */
export const THUMB_GAP_VAR = "--loom-thumb-gap";

/**
 * Custom property carrying the edge length of the image box.
 *
 * Published even though it is the inset minus the gap, because the image has
 * to be bounded in absolute lengths: it hangs in a `Badge`, which MUI gives
 * `flex-shrink: 0`, so a percentage bound resolves against a box that is
 * sized by the image itself and clamps nothing - a 4:3 thumbnail bounded only
 * in height then comes out a third wider than its slot and overlaps the last
 * field.
 */
export const THUMB_SIZE_VAR = "--loom-thumb-size";

const THUMB_GAP = "0.75rem";

/** The column's divider, which is part of the width it reserves: the slot is
 *  `border-box`, so a border left out of the inset would come off the image
 *  box and let a full-width image overhang it. */
const THUMB_BORDER = "1px";

/** Edge length of the image box. A reserved slot is as tall as it is wide and
 *  sets the row's height, so it follows the density like the rhythm does. */
const THUMB_SIZE: Record<NamedDensity, string> = {
    compact: "4rem",
    standard: "6rem",
    full: "8rem",
};

/** Width of a column that has never been dragged, in `fr`. */
export const DEFAULT_COLUMN_WIDTH = 1;

/** Narrowest a column may be dragged, in pixels. Below this the value is all
 *  ellipsis and the column can no longer be grabbed back. */
export const MIN_COLUMN_PX = 48;

/**
 * Whether `width` can be rendered as a track.
 *
 * Widths are read back from local storage, where a value from an older build
 * or a hand-edited entry can be sitting, and one unusable number poisons the
 * whole template: `grid-template-columns: var(…)` is then invalid at
 * computed-value time, which the browser resolves by dropping the property
 * altogether and laying every column out as one.
 */
const isUsableWidth = (width: number | null | undefined): width is number =>
    typeof width === "number" && Number.isFinite(width) && width > 0;

/** Visibility flags that decide whether a thumbnail slot exists. */
export interface ThumbnailSlotVisibility {
    showFieldSections: boolean;
    showThumbnails: boolean;
}

/**
 * Whether the list reserves a thumbnail slot on every card.
 *
 * The list, the header and the cards all answer this from the same store
 * state rather than from what they happen to render: a card that claims a
 * slot the list did not reserve pushes its own columns out of line with every
 * other card. That is why the highlighted card, which otherwise shows every
 * element regardless of the toggles, has no say here.
 */
export const reservesThumbnailSlot = (
    fieldLayout: FieldLayout,
    visibility: ThumbnailSlotVisibility,
): boolean =>
    fieldLayout === "line" &&
    visibility.showFieldSections &&
    visibility.showThumbnails;

/**
 * The reserved width, as custom properties for the list container.
 *
 * The inset is built from the image box and the gap rather than stated on its
 * own, so the width the header skips and the width a card holds free cannot
 * drift apart. `draggedPx` is the edge length the reader left the column's
 * border at, and takes precedence over the density's.
 */
export const thumbnailSlotStyle = (
    density: NamedDensity,
    reserve: boolean,
    draggedPx: number | null,
): CSSProperties => {
    if (!reserve) {
        return {
            [THUMB_INSET_VAR]: "0px",
            [THUMB_GAP_VAR]: "0px",
            [THUMB_SIZE_VAR]: "0px",
        } as CSSProperties;
    }
    const size = isUsableWidth(draggedPx)
        ? `${draggedPx}px`
        : THUMB_SIZE[density];
    return {
        [THUMB_INSET_VAR]: `calc(${size} + ${THUMB_GAP} + ${THUMB_BORDER})`,
        [THUMB_GAP_VAR]: THUMB_GAP,
        [THUMB_SIZE_VAR]: size,
    } as CSSProperties;
};

/**
 * The width of each of `fields`, in `fr`.
 *
 * Widths are kept per field id rather than per position, so dragging a column
 * and then reordering or deselecting fields leaves the remaining ones at the
 * width they were given.
 */
export const columnWidthsOf = (
    fields: string[],
    widths: Record<string, number>,
): number[] =>
    fields.map((id) =>
        isUsableWidth(widths[id]) ? widths[id] : DEFAULT_COLUMN_WIDTH,
    );

/**
 * `grid-template-columns` for columns of the given `fr` widths.
 *
 * `minmax(0, …fr)` rather than a bare `…fr`: a column whose minimum is its
 * content refuses to shrink below a long value, which would push the later
 * columns of that one card out of line with the rest of the list.
 */
export const fieldColumnTemplate = (widths: number[]): string =>
    widths.length === 0
        ? `minmax(0, ${DEFAULT_COLUMN_WIDTH}fr)`
        : widths.map((width) => `minmax(0, ${width}fr)`).join(" ");

/**
 * `widths` with the border between column `index` and the next moved by
 * `delta` fr.
 *
 * Only that pair changes and their sum is kept, so the drag cannot change the
 * total track width: the columns left alone keep their width, the row still
 * fits, and the thumbnail slot stays where it is. A drag that would push
 * either of the two below `min` stops at `min` instead, and one that cannot
 * honour `min` on both at once is refused outright.
 */
export const resizeColumns = (
    widths: number[],
    index: number,
    delta: number,
    min: number,
): number[] => {
    const left = widths[index];
    const right = widths[index + 1];
    if (left == null || right == null) return widths;
    const smallestDelta = min - left;
    const largestDelta = right - min;
    if (largestDelta < smallestDelta) return widths;
    const applied = Math.min(Math.max(delta, smallestDelta), largestDelta);
    const next = [...widths];
    next[index] = left + applied;
    next[index + 1] = right - applied;
    return next;
};
