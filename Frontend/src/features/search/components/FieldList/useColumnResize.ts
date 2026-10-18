import {
    RefObject,
    PointerEvent as ReactPointerEvent,
    useCallback,
    useRef,
} from "react";

import { useAppDispatch } from "@app/hooks";
import {
    setFieldColumnWidths,
    setThumbnailColumnWidth,
} from "@app/slices/searchSlice";

import {
    COLUMN_HOST_ATTR,
    FIELD_COLUMNS_VAR,
    MIN_COLUMN_PX,
    THUMB_INSET_VAR,
    THUMB_SIZE_VAR,
    columnWidthsOf,
    fieldColumnTemplate,
    resizeColumns,
} from "./fieldColumns";

export interface ColumnResize {
    /** Ref for the grid whose tracks are being dragged. */
    gridRef: RefObject<HTMLDivElement | null>;
    /** Pointer-down handler for the handle on the border right of column
     *  `index`. */
    startResize: (index: number) => (event: ReactPointerEvent) => void;
    /** Double-click handler for the same border: splits the width of the two
     *  columns it separates evenly between them. */
    resetBorder: (index: number) => () => void;
    /** Pointer-down handler for the handle on the thumbnail column's border.
     *  That column is a fixed width rather than a share of the row, so it is
     *  dragged in pixels and the field columns absorb what it takes. */
    startThumbnailResize: (event: ReactPointerEvent) => void;
    /** Double-click handler for the same border: hands the column's width
     *  back to the density preset. */
    resetThumbnail: () => void;
}

/**
 * Dragging the border between two column headers.
 *
 * The drag paints the new template straight onto the element that publishes
 * it and only dispatches once the pointer is released. Every card inherits
 * that variable, so going through the store on each pointer event would
 * re-render the whole result list to move one border.
 */
export const useColumnResize = (
    fields: string[],
    widths: Record<string, number>,
): ColumnResize => {
    const dispatch = useAppDispatch();
    const gridRef = useRef<HTMLDivElement>(null);

    const commit = useCallback(
        (next: number[]) => {
            dispatch(
                setFieldColumnWidths(
                    Object.fromEntries(
                        fields.map((id, i) => [id, next[i]] as const),
                    ),
                ),
            );
        },
        [dispatch, fields],
    );

    const startResize = useCallback(
        (index: number) => (event: ReactPointerEvent) => {
            const grid = gridRef.current;
            if (!grid || event.button !== 0) return;
            // The handle lies over the label, which sorts by its field.
            event.preventDefault();
            event.stopPropagation();

            const tracks = getComputedStyle(grid)
                .gridTemplateColumns.split(" ")
                .map(parseFloat);
            const totalPx = tracks.reduce((sum, px) => sum + px, 0);
            const start = columnWidthsOf(fields, widths);
            const totalFr = start.reduce((sum, fr) => sum + fr, 0);
            if (!totalPx || !totalFr) return;
            // The tracks are fr, the pointer moves in px, and the list may be
            // any width: one conversion, fixed for the length of the drag.
            const frPerPx = totalFr / totalPx;
            const host = grid.closest<HTMLElement>(`[${COLUMN_HOST_ATTR}]`);
            const startX = event.clientX;
            const handle = event.currentTarget as HTMLElement;
            handle.setPointerCapture(event.pointerId);

            let latest = start;
            let frame = 0;
            const paint = (clientX: number) => {
                frame = 0;
                latest = resizeColumns(
                    start,
                    index,
                    (clientX - startX) * frPerPx,
                    MIN_COLUMN_PX * frPerPx,
                );
                host?.style.setProperty(
                    FIELD_COLUMNS_VAR,
                    fieldColumnTemplate(latest),
                );
            };
            // Pointer events outrun layout; coalescing to a frame keeps a fast
            // drag from re-laying out the list several times per paint.
            const onMove = (moveEvent: PointerEvent) => {
                const { clientX } = moveEvent;
                if (frame) cancelAnimationFrame(frame);
                frame = requestAnimationFrame(() => paint(clientX));
            };
            const onEnd = () => {
                if (frame) cancelAnimationFrame(frame);
                handle.removeEventListener("pointermove", onMove);
                handle.removeEventListener("pointerup", onEnd);
                handle.removeEventListener("pointercancel", onEnd);
                commit(latest);
            };
            handle.addEventListener("pointermove", onMove);
            handle.addEventListener("pointerup", onEnd);
            handle.addEventListener("pointercancel", onEnd);
        },
        [commit, fields, widths],
    );

    const resetBorder = useCallback(
        (index: number) => () => {
            const start = columnWidthsOf(fields, widths);
            if (start[index] == null || start[index + 1] == null) return;
            const even = (start[index] + start[index + 1]) / 2;
            const next = [...start];
            next[index] = even;
            next[index + 1] = even;
            commit(next);
        },
        [commit, fields, widths],
    );

    const startThumbnailResize = useCallback(
        (event: ReactPointerEvent) => {
            const grid = gridRef.current;
            if (!grid || event.button !== 0) return;
            event.preventDefault();
            event.stopPropagation();

            const handle = event.currentTarget as HTMLElement;
            // The handle sits in the column it resizes, which is the only
            // place its current width can be read from: the custom property
            // holds a length in whatever unit the density used, unresolved.
            const column = handle.parentElement;
            if (!column) return;
            const columnStyle = getComputedStyle(column);
            const gapPx = parseFloat(columnStyle.paddingLeft) || 0;
            const borderPx = parseFloat(columnStyle.borderLeftWidth) || 0;
            // clientWidth is the border box without the border, so this is
            // the image box itself rather than the width reserved for it.
            const startSize = column.clientWidth - gapPx;
            // Never past half the row: the fields have to stay readable, and
            // a column dragged over the whole row cannot be dragged back.
            const maxSize = (grid.clientWidth + column.offsetWidth) / 2;
            const host = grid.closest<HTMLElement>(`[${COLUMN_HOST_ATTR}]`);
            const startX = event.clientX;
            handle.setPointerCapture(event.pointerId);

            let latest = startSize;
            let frame = 0;
            const paint = (clientX: number) => {
                frame = 0;
                // Dragging the border leftwards widens the column, because
                // the column is the side of the border that lies to the right.
                latest = Math.min(
                    Math.max(startSize - (clientX - startX), MIN_COLUMN_PX),
                    maxSize,
                );
                host?.style.setProperty(THUMB_SIZE_VAR, `${latest}px`);
                host?.style.setProperty(
                    THUMB_INSET_VAR,
                    `${latest + gapPx + borderPx}px`,
                );
            };
            const onMove = (moveEvent: PointerEvent) => {
                const { clientX } = moveEvent;
                if (frame) cancelAnimationFrame(frame);
                frame = requestAnimationFrame(() => paint(clientX));
            };
            const onEnd = () => {
                if (frame) cancelAnimationFrame(frame);
                handle.removeEventListener("pointermove", onMove);
                handle.removeEventListener("pointerup", onEnd);
                handle.removeEventListener("pointercancel", onEnd);
                dispatch(setThumbnailColumnWidth(latest));
            };
            handle.addEventListener("pointermove", onMove);
            handle.addEventListener("pointerup", onEnd);
            handle.addEventListener("pointercancel", onEnd);
        },
        [dispatch],
    );

    const resetThumbnail = useCallback(() => {
        dispatch(setThumbnailColumnWidth(null));
    }, [dispatch]);

    return {
        gridRef,
        startResize,
        resetBorder,
        startThumbnailResize,
        resetThumbnail,
    };
};
