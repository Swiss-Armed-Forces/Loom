import { Tooltip, TooltipProps } from "@mui/material";
import {
    cloneElement,
    FocusEvent,
    PointerEvent,
    useCallback,
    useState,
} from "react";

interface ChildHandlers {
    onPointerEnter?: (event: PointerEvent<HTMLElement>) => void;
    onPointerLeave?: (event: PointerEvent<HTMLElement>) => void;
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
 * Drop-in for `Tooltip`. The child must accept a ref and event handlers, which
 * `Tooltip` requires of its child anyway.
 */
export const LazyTooltip = ({ children, ...tooltipProps }: TooltipProps) => {
    const [armed, setArmed] = useState(false);
    const [open, setOpen] = useState(false);

    const show = useCallback(() => {
        setArmed(true);
        setOpen(true);
    }, []);
    const hide = useCallback(() => setOpen(false), []);

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
