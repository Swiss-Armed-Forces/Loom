/** Narrowest a sidebar may be dragged. */
export const MIN_SIDEBAR_WIDTH = 14 * 16;
/** Width the centre column is never squeezed below, which is what bounds how
 *  wide a sidebar may be dragged on the current viewport. */
const CENTER_MIN_WIDTH = 20 * 16;

export const DEFAULT_LEFT_SIDEBAR_WIDTH = 20 * 16;
export const DEFAULT_RIGHT_SIDEBAR_WIDTH = 28 * 16;

/**
 * Clamp a sidebar width to the viewport.
 *
 * The upper bound depends on `window.innerWidth`, so a width persisted on a
 * wide screen has to be clamped again when it is read back on a narrow one.
 */
export const clampSidebarWidth = (width: number): number => {
    const effectiveMax = Math.max(
        MIN_SIDEBAR_WIDTH,
        window.innerWidth - CENTER_MIN_WIDTH,
    );
    return Math.min(effectiveMax, Math.max(MIN_SIDEBAR_WIDTH, width));
};
