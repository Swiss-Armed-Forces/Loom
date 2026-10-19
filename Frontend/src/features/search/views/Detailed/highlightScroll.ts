/**
 * How the highlighted card is placed in the scroll container.
 *
 * The scrolling itself belongs to the virtualizer: it knows where every row
 * starts and how tall it is, measured or estimated, and it keeps re-resolving
 * the target as rows are measured for real. All that is left here is which
 * edge to align to, which is a rule rather than a measurement and so stays
 * testable without a layout engine, which jsdom does not have.
 */

/**
 * Gap kept between the card and the edge it is aligned to.
 *
 * Handed to the virtualizer as its scroll padding. The same gap is written as
 * `scroll-padding` on `.searchPanel` in `CenterTabs.module.css`, for the
 * pending page row, which sits outside the virtual list and is placed by the
 * browser's own `scrollIntoView`; the two have to be changed together.
 */
export const SCROLL_PADDING_PX = 48;

export type HighlightScrollMode = "smart" | "top";

/** What the virtualizer is asked to align the highlighted row to. */
export type HighlightAlign = "start" | "auto";

/**
 * Which edge to align the highlighted row to.
 *
 * `auto` is the virtualizer's own dead band: a row already clear of the scroll
 * padding at both ends is left exactly where it is, so walking the list with
 * the arrow keys does not drag the viewport along behind a card that is
 * perfectly readable where it sits. It covers everything but a card taller
 * than the band — aligning the bottom of one of those would put its beginning
 * off screen, so they go to the top instead. `top` always aligns to the top,
 * which is what a jump from somewhere else — the folder tree, the chat —
 * wants.
 */
export const alignForHighlight = (
    itemSize: number,
    viewportHeight: number,
    mode: HighlightScrollMode,
): HighlightAlign =>
    mode === "top" || itemSize > viewportHeight - 2 * SCROLL_PADDING_PX
        ? "start"
        : "auto";
