import { FolderTree, PATH_SEPARATOR } from "./folderViewState";

/**
 * Returns the IDs of all ancestor nodes (including the root, excluding the
 * matched node itself) for the tree node whose fileId matches the given value,
 * or null if no such node exists.
 *
 * Uses an iterative DFS to avoid call-stack overflow on deeply nested trees.
 */
export const findAncestorNodeIds = (
    tree: FolderTree,
    fileId: string,
): string[] | null => {
    const stack: Array<{ node: FolderTree; ancestors: string[] }> = [
        { node: tree, ancestors: [] },
    ];
    while (stack.length > 0) {
        const { node, ancestors } = stack.pop()!;
        if (node.fileId === fileId) return ancestors;
        for (const child of Object.values(node.children ?? {})) {
            stack.push({ node: child, ancestors: [...ancestors, node.id] });
        }
    }
    return null;
};

/**
 * Returns the tree node with the given path ID, or undefined if not found.
 *
 * Uses an iterative DFS to avoid call-stack overflow on deeply nested trees.
 */
export const findTreeNode = (
    tree: FolderTree | null | undefined,
    path: string,
): FolderTree | undefined => {
    if (!tree) return undefined;
    const stack: FolderTree[] = [tree];
    while (stack.length > 0) {
        const node = stack.pop()!;
        if (node.id === path) return node;
        for (const child of Object.values(node.children ?? {})) {
            stack.push(child);
        }
    }
    return undefined;
};

/**
 * Returns a new tree with structural sharing: only nodes on the path from the
 * root to `targetPath` are cloned; all other subtrees keep their existing
 * references, making this O(depth) instead of O(n).
 */
export const cloneSpineToPath = (
    tree: FolderTree,
    targetPath: string,
): FolderTree => {
    const cloned: FolderTree = { ...tree };
    if (!tree.children) return cloned;

    const newChildren: Record<string, FolderTree> = {};
    let spineFound = false;
    for (const [key, child] of Object.entries(tree.children)) {
        const isOnSpine =
            child.id === targetPath ||
            targetPath.startsWith(child.id + PATH_SEPARATOR);
        if (isOnSpine) {
            newChildren[key] = cloneSpineToPath(child, targetPath);
            spineFound = true;
        } else {
            newChildren[key] = child;
        }
    }
    cloned.children = spineFound ? newChildren : { ...tree.children };
    return cloned;
};

export const cloneTree = (tree: FolderTree): typeof tree => {
    if (!tree) {
        return tree;
    }

    return {
        ...tree,
        children: tree.children
            ? Object.fromEntries(
                  Object.values(tree.children)
                      .map(cloneTree)
                      .filter(Boolean)
                      .map((child) => [child.id, child]),
              )
            : undefined,
    };
};
