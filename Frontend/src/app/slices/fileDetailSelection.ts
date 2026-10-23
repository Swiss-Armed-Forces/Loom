/**
 * Which tab of the File Detail sidebar is in front.
 *
 * The strip is one leftmost tab that cannot be closed, plus the tabs the
 * reader opened. That first one has no file of its own: it shows whatever is
 * highlighted and changes under the reader as the highlight moves. That is why
 * it is a *kind* and not a file id - anything that wants the file has to say
 * which highlight it is reading, through `selectedFileIdOf`.
 *
 * Called the *following* tab in code, which is what it does; the pin it is
 * drawn with says only that it stays where it is.
 *
 * Lives in its own module so the helpers can be shared by the slice, the view
 * and the keyboard without pulling in the slice.
 */
export type FileDetailSelection =
    | { readonly kind: "follow" }
    | { readonly kind: "file"; readonly fileId: string };

/** The following tab, as one shared value: a fresh object per read would make
 *  every memoised consumer re-render on an unchanged state. */
export const FOLLOW_TAB: FileDetailSelection = Object.freeze({
    kind: "follow",
});

export const fileTab = (fileId: string): FileDetailSelection => ({
    kind: "file",
    fileId,
});

export const sameSelection = (
    a: FileDetailSelection,
    b: FileDetailSelection,
): boolean =>
    a.kind === "follow"
        ? b.kind === "follow"
        : b.kind === "file" && a.fileId === b.fileId;

/**
 * The file a selection shows.
 *
 * Null only for the following tab with nothing highlighted - the one state in
 * which the sidebar has a tab but no file, and draws the placeholder.
 */
export const selectedFileIdOf = (
    selection: FileDetailSelection,
    highlightedFileId: string | null,
): string | null =>
    selection.kind === "follow" ? highlightedFileId : selection.fileId;

/**
 * Stable React key and cache key for a tab.
 *
 * Unique across the strip by construction: the selection space *is* the tab
 * set, and a file id cannot collide with `follow` because of the prefix.
 */
export const selectionKey = (selection: FileDetailSelection): string =>
    selection.kind === "follow" ? "follow" : `file:${selection.fileId}`;
