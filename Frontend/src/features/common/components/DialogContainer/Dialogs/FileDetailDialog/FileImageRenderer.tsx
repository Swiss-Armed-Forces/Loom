import { Box } from "@mui/material";
import {
    forwardRef,
    KeyboardEvent as ReactKeyboardEvent,
    useCallback,
    useEffect,
    useImperativeHandle,
    useRef,
} from "react";

import { clamp } from "@features/common/utils/helpers";
import { Point, Size } from "@features/common/utils/model";

import { ContentRendererRef } from "./contentRendererRef";
import {
    anchoredPan,
    clampPan,
    isPannable,
    renderedSize,
    topAnchoredPan,
} from "./imageViewport";
import { wheelDeltaInPixels, wheelZoomFactor } from "./previewZoom";

interface FileImageRendererProps {
    src: string;
}

const MIN_ZOOM = 0.25;
const MAX_ZOOM = 5;
const BUTTON_ZOOM_STEP = 0.25;

// How far a single arrow key press pans the image.
const KEY_PAN_STEP = 48;

export const FileImageRenderer = forwardRef<
    ContentRendererRef,
    FileImageRendererProps
>(function FileImageRenderer({ src }, ref) {
    const containerRef = useRef<HTMLDivElement>(null);
    const imgRef = useRef<HTMLImageElement>(null);
    const zoomRef = useRef(1);
    const rotationRef = useRef(0);
    const panRef = useRef<Point>({ x: 0, y: 0 });
    // The pointer currently dragging the image, or null when idle. Holding the
    // id keeps a second finger from hijacking an ongoing drag.
    const dragPointerRef = useRef<number | null>(null);
    const lastPointerRef = useRef<Point>({ x: 0, y: 0 });

    // The viewport the image is panned within. The padding sits on an inner
    // wrapper so that this is the true frame size, not a padded one.
    const getFrameSize = useCallback((): Size => {
        const container = containerRef.current;
        if (!container) return { width: 0, height: 0 };
        return {
            width: container.clientWidth,
            height: container.clientHeight,
        };
    }, []);

    const getRenderedSize = useCallback((): Size => {
        const img = imgRef.current;
        if (!img) return { width: 0, height: 0 };
        return renderedSize(
            { width: img.offsetWidth, height: img.offsetHeight },
            zoomRef.current,
            rotationRef.current,
        );
    }, []);

    const applyTransform = useCallback(() => {
        const img = imgRef.current;
        const container = containerRef.current;
        if (!img || !container) return;

        const rendered = getRenderedSize();
        const frame = getFrameSize();
        panRef.current = clampPan(panRef.current, rendered, frame);
        const { x, y } = panRef.current;
        img.style.transform = `translate(${x}px, ${y}px) rotate(${rotationRef.current}deg) scale(${zoomRef.current})`;

        container.style.cursor =
            dragPointerRef.current !== null
                ? "grabbing"
                : isPannable(rendered, frame)
                  ? "grab"
                  : "default";
    }, [getFrameSize, getRenderedSize]);

    const setZoom = useCallback(
        (zoom: number, anchor?: Point) => {
            const nextZoom = clamp(zoom, MIN_ZOOM, MAX_ZOOM);
            const container = containerRef.current;
            if (container) {
                // Without an anchor the change came from the toolbar, where the
                // centre of the frame is the natural invariant point.
                const rect = container.getBoundingClientRect();
                const anchorOffset: Point = anchor
                    ? {
                          x: anchor.x - (rect.left + rect.width / 2),
                          y: anchor.y - (rect.top + rect.height / 2),
                      }
                    : { x: 0, y: 0 };
                panRef.current = anchoredPan(
                    panRef.current,
                    anchorOffset,
                    nextZoom / zoomRef.current,
                );
            }
            zoomRef.current = nextZoom;
            applyTransform();
        },
        [applyTransform],
    );

    const handleWheel = useCallback(
        (event: WheelEvent) => {
            const container = containerRef.current;
            if (!container) return;

            // Cmd is the zoom idiom on macOS, Ctrl everywhere else.
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                const pixels = wheelDeltaInPixels(
                    event.deltaY,
                    event.deltaMode,
                    container.clientHeight,
                );
                setZoom(zoomRef.current * wheelZoomFactor(pixels), {
                    x: event.clientX,
                    y: event.clientY,
                });
                return;
            }

            // Without a modifier the wheel pans, but only over the part of the
            // image that is out of frame.
            const frame = getFrameSize();
            if (!isPannable(getRenderedSize(), frame)) return;
            event.preventDefault();
            panRef.current = {
                x:
                    panRef.current.x -
                    wheelDeltaInPixels(
                        event.deltaX,
                        event.deltaMode,
                        frame.width,
                    ),
                y:
                    panRef.current.y -
                    wheelDeltaInPixels(
                        event.deltaY,
                        event.deltaMode,
                        frame.height,
                    ),
            };
            applyTransform();
        },
        [setZoom, applyTransform, getFrameSize, getRenderedSize],
    );

    const handlePointerDown = useCallback(
        (event: PointerEvent) => {
            // Left button drags the image, middle button (wheel click) does the
            // same for users who expect the classic viewer behaviour. Touch and
            // pen contacts both report button 0.
            if (event.button !== 0 && event.button !== 1) return;
            const container = containerRef.current;
            if (!container) return;
            // Nothing to drag while the image fits, and suppressing the default
            // would then needlessly swallow the click.
            if (!isPannable(getRenderedSize(), getFrameSize())) return;

            dragPointerRef.current = event.pointerId;
            lastPointerRef.current = { x: event.clientX, y: event.clientY };
            // Capture routes the rest of the gesture here even when the pointer
            // leaves the frame or the window, and guarantees a pointerup or
            // pointercancel to end the drag with.
            container.setPointerCapture(event.pointerId);
            container.focus();
            applyTransform();
            // Suppresses the browser's native image drag, the middle click
            // autoscroll and touch scrolling.
            event.preventDefault();
        },
        [applyTransform, getFrameSize, getRenderedSize],
    );

    const handlePointerMove = useCallback(
        (event: PointerEvent) => {
            if (event.pointerId !== dragPointerRef.current) return;
            panRef.current = {
                x: panRef.current.x + event.clientX - lastPointerRef.current.x,
                y: panRef.current.y + event.clientY - lastPointerRef.current.y,
            };
            lastPointerRef.current = { x: event.clientX, y: event.clientY };
            applyTransform();
            event.preventDefault();
        },
        [applyTransform],
    );

    const handlePointerUp = useCallback(
        (event: PointerEvent) => {
            if (event.pointerId !== dragPointerRef.current) return;
            dragPointerRef.current = null;
            containerRef.current?.releasePointerCapture(event.pointerId);
            applyTransform();
        },
        [applyTransform],
    );

    const handleKeyDown = useCallback(
        (event: ReactKeyboardEvent<HTMLDivElement>) => {
            const rendered = getRenderedSize();
            const frame = getFrameSize();
            // Let the global shortcuts have the key when there is nothing to
            // pan.
            if (!isPannable(rendered, frame)) return;

            const pan = panRef.current;
            const top = topAnchoredPan(rendered, frame).y;
            let next: Point;
            switch (event.key) {
                case "ArrowUp":
                    next = { x: pan.x, y: pan.y + KEY_PAN_STEP };
                    break;
                case "ArrowDown":
                    next = { x: pan.x, y: pan.y - KEY_PAN_STEP };
                    break;
                case "ArrowLeft":
                    next = { x: pan.x + KEY_PAN_STEP, y: pan.y };
                    break;
                case "ArrowRight":
                    next = { x: pan.x - KEY_PAN_STEP, y: pan.y };
                    break;
                case "PageUp":
                    next = { x: pan.x, y: pan.y + frame.height };
                    break;
                case "PageDown":
                    next = { x: pan.x, y: pan.y - frame.height };
                    break;
                case "Home":
                    next = { x: pan.x, y: top };
                    break;
                case "End":
                    next = { x: pan.x, y: -top };
                    break;
                default:
                    return;
            }
            panRef.current = next;
            applyTransform();
            event.preventDefault();
        },
        [applyTransform, getFrameSize, getRenderedSize],
    );

    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        container.addEventListener("wheel", handleWheel, { passive: false });
        container.addEventListener("pointerdown", handlePointerDown);
        container.addEventListener("pointermove", handlePointerMove);
        container.addEventListener("pointerup", handlePointerUp);
        container.addEventListener("pointercancel", handlePointerUp);

        // A shrinking frame can leave the image outside of it, so re-clamp.
        const observer = new ResizeObserver(() => applyTransform());
        observer.observe(container);

        return () => {
            container.removeEventListener("wheel", handleWheel);
            container.removeEventListener("pointerdown", handlePointerDown);
            container.removeEventListener("pointermove", handlePointerMove);
            container.removeEventListener("pointerup", handlePointerUp);
            container.removeEventListener("pointercancel", handlePointerUp);
            observer.disconnect();
        };
    }, [
        handleWheel,
        handlePointerDown,
        handlePointerMove,
        handlePointerUp,
        applyTransform,
    ]);

    const resetView = useCallback(() => {
        zoomRef.current = 1;
        rotationRef.current = 0;
        panRef.current = topAnchoredPan(getRenderedSize(), getFrameSize());
        applyTransform();
    }, [applyTransform, getFrameSize, getRenderedSize]);

    useEffect(() => {
        resetView();
    }, [src, resetView]);

    useImperativeHandle(ref, () => ({
        zoomIn: () => setZoom(zoomRef.current + BUTTON_ZOOM_STEP),
        zoomOut: () => setZoom(zoomRef.current - BUTTON_ZOOM_STEP),
        zoomReset: resetView,
        rotate: () => {
            rotationRef.current = (rotationRef.current + 90) % 360;
            applyTransform();
        },
    }));

    return (
        <Box
            ref={containerRef}
            tabIndex={0}
            onKeyDown={handleKeyDown}
            sx={{
                flex: 1,
                minHeight: 0,
                overflow: "hidden",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                // The frame handles every pan gesture itself, so the browser
                // must not claim touch gestures for scrolling.
                touchAction: "none",
            }}
        >
            <Box sx={{ p: 1, width: "100%", flexShrink: 0 }}>
                <img
                    ref={imgRef}
                    src={src}
                    alt="Rendered file"
                    draggable={false}
                    // Size is only known once the image is decoded, and the
                    // reset depends on it.
                    onLoad={resetView}
                    style={{
                        display: "block",
                        width: "100%",
                        maxWidth: "none",
                        transformOrigin: "center center",
                        userSelect: "none",
                    }}
                />
            </Box>
        </Box>
    );
});
