import { clamp } from "@features/common/utils/helpers";
import { Point, Size } from "@features/common/utils/model";

// Geometry of the zoomable image viewport. Kept free of DOM access so the
// arithmetic can be tested without a layout engine; the component only reads
// the measurements out of the DOM and writes the resulting transform back.

/**
 * Size the image occupies on screen once zoom and rotation are applied. A
 * quarter turn swaps the axes, a half turn leaves them as they are.
 */
export const renderedSize = (
    layout: Size,
    zoom: number,
    rotation: number,
): Size => {
    const quarterTurned = rotation % 180 !== 0;
    return {
        width: (quarterTurned ? layout.height : layout.width) * zoom,
        height: (quarterTurned ? layout.width : layout.height) * zoom,
    };
};

/** Whether the image sticks out of the frame on either axis. */
export const isPannable = (rendered: Size, frame: Size): boolean =>
    rendered.width > frame.width || rendered.height > frame.height;

/**
 * The image is centred in the frame and panning moves it away from that centre.
 * Limiting the offset to the half of the image that hangs out of the frame
 * keeps an edge glued to the frame, so it can never be pushed out of view -
 * whatever the current zoom or rotation is. An image that fits gets a
 * zero-width window and cannot be nudged at all.
 */
export const clampPan = (pan: Point, rendered: Size, frame: Size): Point => {
    const maxX = Math.max(0, (rendered.width - frame.width) / 2);
    const maxY = Math.max(0, (rendered.height - frame.height) / 2);
    return {
        x: clamp(pan.x, -maxX, maxX),
        y: clamp(pan.y, -maxY, maxY),
    };
};

/**
 * Pan offset that puts the top edge of the image at the top of the frame. A
 * scanned page is the common payload here and its header is the part worth
 * seeing first, so this is where the view starts and returns to on reset.
 */
export const topAnchoredPan = (rendered: Size, frame: Size): Point => ({
    x: 0,
    y: Math.max(0, (rendered.height - frame.height) / 2),
});

/**
 * Pan that keeps the point under `anchorOffset` - measured from the centre of
 * the frame - over the same pixel of the image while the zoom changes by
 * `ratio`. The offset between the anchor and the image centre grows with the
 * same ratio as the zoom itself.
 *
 * `ratio` must come from the *clamped* zoom: at a zoom bound it is then exactly
 * 1 and the pan is returned unchanged, so the image cannot creep while the
 * wheel keeps spinning against the bound.
 */
export const anchoredPan = (
    pan: Point,
    anchorOffset: Point,
    ratio: number,
): Point => ({
    x: anchorOffset.x - (anchorOffset.x - pan.x) * ratio,
    y: anchorOffset.y - (anchorOffset.y - pan.y) * ratio,
});
