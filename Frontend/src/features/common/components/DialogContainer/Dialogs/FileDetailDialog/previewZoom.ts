import { clamp } from "@features/common/utils/helpers";

// Wheel zoom behaviour shared by every file preview renderer, so the image and
// the PDF preview in the same dialog zoom at the same pace.

// One full wheel notch changes the zoom by 15%.
const WHEEL_ZOOM_FACTOR = 1.15;

// Wheel delta that makes up one full zoom step. Chrome reports ~100px per
// notch, which is the reference this is calibrated against.
const PIXELS_PER_ZOOM_STEP = 100;

// Nominal line height used to turn Firefox's line based deltas into pixels.
// Firefox derives its own value from the computed line-height of the event
// target, so this is an approximation rather than a spec value: it trades an
// exact match for not having to measure the target on every wheel event.
const NOMINAL_LINE_HEIGHT = 16;

/**
 * Normalises a wheel delta to pixels. Firefox reports lines, and a few
 * configurations report pages, so the raw delta is not comparable across
 * browsers.
 *
 * `pageSize` is the size of the viewport along the axis of the delta.
 */
export const wheelDeltaInPixels = (
    delta: number,
    deltaMode: number,
    pageSize: number,
): number => {
    if (deltaMode === WheelEvent.DOM_DELTA_LINE)
        return delta * NOMINAL_LINE_HEIGHT;
    if (deltaMode === WheelEvent.DOM_DELTA_PAGE) return delta * pageSize;
    return delta;
};

/**
 * The most a single event may move the zoom, in pixels.
 *
 * A momentum flick and a DOM_DELTA_PAGE event both carry a delta far beyond
 * anything a deliberate gesture produces - a page delta is a whole viewport,
 * which unbounded is a factor of three in one event, i.e. most of the zoom
 * range in a single tick. Two notches is fast but still reads as a zoom.
 */
const MAX_ZOOM_PIXELS = 2 * PIXELS_PER_ZOOM_STEP;

/**
 * Zoom factor for a wheel delta, continuous in the delta so that a trackpad
 * pinch (many tiny deltas) and a notched wheel (few large ones) travel the same
 * distance for the same amount of scrolling. A negative delta - scrolling up -
 * zooms in.
 */
export const wheelZoomFactor = (deltaInPixels: number): number =>
    Math.pow(
        WHEEL_ZOOM_FACTOR,
        -clamp(deltaInPixels, -MAX_ZOOM_PIXELS, MAX_ZOOM_PIXELS) /
            PIXELS_PER_ZOOM_STEP,
    );
