import { Tooltip, TooltipProps } from "@mui/material";
import {
    cloneElement,
    FocusEvent,
    PointerEvent,
    useCallback,
    useEffect,
    useRef,
    useState,
} from "react";

interface ChildHandlers {
    onPointerEnter?: (event: PointerEvent<HTMLElement>) => void;
    onPointerLeave?: (event: PointerEvent<HTMLElement>) => void;
    onPointerDown?: (event: PointerEvent<HTMLElement>) => void;
    onPointerUp?: (event: PointerEvent<HTMLElement>) => void;
    onPointerCancel?: (event: PointerEvent<HTMLElement>) => void;
    onFocus?: (event: FocusEvent<HTMLElement>) => void;
    onBlur?: (event: FocusEvent<HTMLElement>) => void;
}

/**
 * A `Tooltip` that costs nothing until the user reaches for it.
 *
 * MUI renders a `Popper` for every `Tooltip`, open or not, and re-renders it
 * with its parent. A result list carries dozens of them and at most one can
 * ever be visible, so the real `Tooltip` is mounted only once the element has
 * been hovered or focused, and stays mounted from then on.
 *
 * Visibility is driven from here rather than left to MUI: by the time we mount
 * the `Tooltip` the pointer is already inside the element, so the `mouseover`
 * MUI opens on has already been and gone. The only visible difference from a
 * plain `Tooltip` is that hovering shows it immediately instead of after
 * `enterDelay`.
 *
 * Arming replaces the element: React sees the child where a `Tooltip` now
 * stands and rebuilds the subtree, so the DOM node under the pointer is
 * swapped for a new one. Land that between `mousedown` and `mouseup` and the
 * browser produces no `click` at all - which is what made the first click on
 * a toolbar button after a page load do nothing. Hover schedules the swap on
 * a short timer rather than doing it in the handler, and a press in progress
 * holds it back until the press is over, so it can never fall inside a
 * click. The timer doubles as the `enterDelay` a plain `Tooltip` has.
 *
 * Drop-in for `Tooltip`. The child must accept a ref and event handlers, which
 * `Tooltip` requires of its child anyway.
 */
/** How long the pointer has to stay before the real `Tooltip` is mounted. */
const ARM_DELAY_MS = 200;

export const LazyTooltip = ({ children, ...tooltipProps }: TooltipProps) => {
    const [armed, setArmed] = useState(false);
    const [open, setOpen] = useState(false);
    const pressedRef = useRef(false);
    const armWhenReleasedRef = useRef(false);
    const armTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const cancelArming = useCallback(() => {
        if (armTimerRef.current === null) return;
        clearTimeout(armTimerRef.current);
        armTimerRef.current = null;
    }, []);

    const show = useCallback(() => {
        setOpen(true);
        if (armTimerRef.current !== null) return;
        armTimerRef.current = setTimeout(() => {
            armTimerRef.current = null;
            if (pressedRef.current) {
                armWhenReleasedRef.current = true;
                return;
            }
            setArmed(true);
        }, ARM_DELAY_MS);
    }, []);
    const hide = useCallback(() => {
        cancelArming();
        setOpen(false);
    }, [cancelArming]);
    const release = useCallback(() => {
        pressedRef.current = false;
        if (!armWhenReleasedRef.current) return;
        armWhenReleasedRef.current = false;
        // After this task, not during it: `click` is dispatched straight after
        // `mouseup`, and a synchronous re-render here would swap the element
        // out before the browser got to it.
        setTimeout(() => setArmed(true), 0);
    }, []);

    useEffect(() => cancelArming, [cancelArming]);

    const childProps = children.props as ChildHandlers;
    const child = cloneElement(children, {
        onPointerEnter: (event: PointerEvent<HTMLElement>) => {
            childProps.onPointerEnter?.(event);
            show();
        },
        onPointerLeave: (event: PointerEvent<HTMLElement>) => {
            childProps.onPointerLeave?.(event);
            hide();
        },
        onPointerDown: (event: PointerEvent<HTMLElement>) => {
            childProps.onPointerDown?.(event);
            pressedRef.current = true;
        },
        onPointerUp: (event: PointerEvent<HTMLElement>) => {
            childProps.onPointerUp?.(event);
            release();
        },
        onPointerCancel: (event: PointerEvent<HTMLElement>) => {
            childProps.onPointerCancel?.(event);
            release();
        },
        onFocus: (event: FocusEvent<HTMLElement>) => {
            childProps.onFocus?.(event);
            show();
        },
        onBlur: (event: FocusEvent<HTMLElement>) => {
            childProps.onBlur?.(event);
            hide();
        },
    } as Partial<TooltipProps["children"]["props"]>);

    if (!armed) return child;

    return (
        <Tooltip {...tooltipProps} open={open} onClose={hide}>
            {child}
        </Tooltip>
    );
};
