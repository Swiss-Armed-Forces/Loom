import { FolderViewOptions } from "@app/slices/searchSlice";

import { FolderTree, PATH_SEPARATOR } from "./folderViewState";

/**
 * Where a node sits relative to the two folder-view limits.
 *
 * `path` counts path segments below the virtual root, so the root's own
 * children are at 1.
 *
 * `extraction` counts container hops: how many of the node's ancestors are
 * themselves files. This is exact rather than heuristic, because path-nesting
 * under a file is precisely what extraction produces — the worker names an
 * attachment `<container full_name>/<attachment name>`.
 *
 * The two do not move together. Tika hands back an archive entry under its own
 * inner path, so `//s/a.zip/inner/report.pdf` is three path segments below the
 * archive but only **one** container hop in, the same as a mail attachment
 * sitting directly beside its message.
 */
export interface NodeDepth {
    path: number;
    extraction: number;
}

/** The virtual root is below both limits by definition — it is always drawn. */
export const ROOT_DEPTH: NodeDepth = { path: 0, extraction: 0 };

/**
 * Depth of a child, from its parent's depth and whether that parent is a file.
 *
 * Derived while walking down rather than by searching upwards, so a node costs
 * O(1) to place however deep the tree is.
 */
export const childDepth = (
    parent: NodeDepth,
    parentIsFile: boolean,
): NodeDepth => ({
    path: parent.path + 1,
    extraction: parent.extraction + (parentIsFile ? 1 : 0),
});

/** Whether a node at this depth survives both limits. `null` is "no limit". */
export const isWithinLimits = (
    depth: NodeDepth,
    limits: FolderViewOptions,
): boolean =>
    (limits.pathDepth === null || depth.path <= limits.pathDepth) &&
    (limits.extractionDepth === null ||
        depth.extraction <= limits.extractionDepth);

/**
 * Whether a flat filename result survives the extraction limit.
 *
 * Filter mode replaces the tree with a flat list, so there are no ancestors to
 * count and the nesting level has to come from the backend instead. The folder
 * limit has no meaning here: the list is not a tree.
 */
export const isWithinExtractionLimit = (
    recursionDepth: number | undefined,
    limits: FolderViewOptions,
): boolean =>
    limits.extractionDepth === null ||
    (recursionDepth ?? 0) <= limits.extractionDepth;

/** Whether either limit is set, i.e. whether the tree is being shortened at all. */
export const hasAnyLimit = (limits: FolderViewOptions): boolean =>
    limits.pathDepth !== null || limits.extractionDepth !== null;

/**
 * Depth of an already-loaded node, found by descending to it.
 *
 * Rendering passes depth down the recursion and never needs this; the callers
 * that do are the ones holding a bare node id — deciding whether a node the
 * user just expanded, or one restored from localStorage, is worth fetching
 * children for.
 *
 * Node ids are full paths and children are keyed by full path, so this follows
 * the one branch that can contain the target rather than searching the whole
 * tree: O(depth × branching) instead of O(nodes).
 */
export const depthOfNode = (
    tree: FolderTree,
    nodeId: string,
): NodeDepth | null => {
    let node = tree;
    let depth = ROOT_DEPTH;
    while (node.id !== nodeId) {
        const next = Object.values(node.children ?? {}).find(
            (child) =>
                child.id === nodeId ||
                nodeId.startsWith(child.id + PATH_SEPARATOR),
        );
        if (next === undefined) return null;
        depth = childDepth(depth, node.fileId !== undefined);
        node = next;
    }
    return depth;
};

/**
 * Whether children of this node would be drawn, so whether fetching them is
 * worth a request.
 *
 * Takes the node the caller already resolved rather than looking it up again.
 */
export const shouldLoadChildrenOf = (
    tree: FolderTree,
    node: FolderTree,
    limits: FolderViewOptions,
): boolean => {
    if (!hasAnyLimit(limits)) return true;
    const depth = depthOfNode(tree, node.id);
    if (depth === null) return true;
    return isWithinLimits(childDepth(depth, node.fileId !== undefined), limits);
};
