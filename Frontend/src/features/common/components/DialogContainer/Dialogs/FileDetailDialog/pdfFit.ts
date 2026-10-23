/**
 * Whether the viewer should be fitted to the width of its container.
 *
 * Fitting asks pdf.js to divide the container's width by the page's, and a
 * container with no layout box makes that zero. pdf.js takes the zero without
 * clamping it, leaves its own scale at the sentinel it uses for "unknown" —
 * which is also zero — and returns early, so the scale is never set at all.
 * Nothing on screen says so: the pages are laid out from a getter that reports
 * an unset scale as 100%, so the document looks right. The first zoom then
 * multiplies the zero and clamps to the minimum, and the page collapses from
 * full width to a tenth of it in one notch.
 *
 * A panel that is hidden while its PDF loads is exactly that case — opening a
 * file in a background tab, or reloading with more than one tab open, or
 * clicking away before the render finishes. So the fit waits for a container
 * with a width, and is taken again when one appears.
 *
 * Once fitted, a later resize must not re-fit: the scale on screen may be one
 * the reader chose, and re-fitting would throw it away.
 */
export const shouldFitToWidth = (
    containerWidth: number,
    hasFitted: boolean,
): boolean => containerWidth > 0 && !hasFitted;
