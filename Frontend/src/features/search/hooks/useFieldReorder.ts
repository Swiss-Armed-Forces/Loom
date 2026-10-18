import { DragEvent, useCallback, useState } from "react";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectPreviewFields, setPreviewFields } from "@app/slices/searchSlice";
import { moveItem } from "@features/common/utils/helpers";

/** Drag type carrying a preview field's position in the selection. */
const FIELD_INDEX_MIME = "application/x-loom-preview-field";

/** What a draggable field element has to spread onto itself. */
export interface FieldDragProps {
    draggable: true;
    onDragStart: (event: DragEvent) => void;
    onDragOver: (event: DragEvent) => void;
    onDrop: (event: DragEvent) => void;
    onDragEnd: () => void;
}

export interface FieldReorder {
    /** Drag handlers for the field at `index` of the selection. */
    dragProps: (index: number) => FieldDragProps;
    /** Whether that field is the one currently being dragged. */
    isDragging: (index: number) => boolean;
    /** Whether a drop on that field is what the pointer is offering. */
    isDropTarget: (index: number) => boolean;
}

/**
 * Reordering the selected preview fields by dragging them.
 *
 * `previewFields` is the order the columns are drawn in, so the chips in the
 * customization panel and the column headers are two views of one list and
 * are dragged with one hook. The position travels in the drag's own data
 * rather than in component state, which is what lets a chip be dropped on a
 * column header and the other way round.
 */
export const useFieldReorder = (): FieldReorder => {
    const dispatch = useAppDispatch();
    const previewFields = useAppSelector(selectPreviewFields);
    const [draggingIndex, setDraggingIndex] = useState<number | null>(null);
    const [dropIndex, setDropIndex] = useState<number | null>(null);

    const dragProps = useCallback(
        (index: number): FieldDragProps => ({
            draggable: true,
            onDragStart: (event) => {
                event.dataTransfer.effectAllowed = "move";
                event.dataTransfer.setData(FIELD_INDEX_MIME, String(index));
                setDraggingIndex(index);
            },
            onDragOver: (event) => {
                // Only a field drag is a drop here; anything else the browser
                // offers - a file, a selection, a link - is left alone.
                if (!event.dataTransfer.types.includes(FIELD_INDEX_MIME)) {
                    return;
                }
                event.preventDefault();
                event.dataTransfer.dropEffect = "move";
                setDropIndex(index);
            },
            onDrop: (event) => {
                if (!event.dataTransfer.types.includes(FIELD_INDEX_MIME)) {
                    return;
                }
                event.preventDefault();
                const from = Number(
                    event.dataTransfer.getData(FIELD_INDEX_MIME),
                );
                setDraggingIndex(null);
                setDropIndex(null);
                if (!Number.isInteger(from)) return;
                const next = moveItem(previewFields, from, index);
                if (next !== previewFields) dispatch(setPreviewFields(next));
            },
            onDragEnd: () => {
                setDraggingIndex(null);
                setDropIndex(null);
            },
        }),
        [dispatch, previewFields],
    );

    const isDragging = useCallback(
        (index: number) => draggingIndex === index,
        [draggingIndex],
    );

    const isDropTarget = useCallback(
        (index: number) => dropIndex === index && draggingIndex !== index,
        [dropIndex, draggingIndex],
    );

    return { dragProps, isDragging, isDropTarget };
};
