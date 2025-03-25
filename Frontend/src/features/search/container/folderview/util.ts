import { FolderTree } from "./folderViewState";

export function findTreeNode(
    tree: FolderTree | null | undefined,
    path: string,
): FolderTree | undefined {
    if (!tree) {
        return undefined;
    }
    if (tree.id === path) {
        return tree;
    } else {
        for (const child of Object.values(tree.children ?? {})) {
            const found = findTreeNode(child, path);
            if (found) return found;
        }
        return undefined;
    }
}

export function cloneTree(tree: FolderTree): typeof tree {
    if (!tree) {
        return tree;
    }

    return {
        ...tree,
        children: tree.children
            ? Object.values(tree.children)
                  .map(cloneTree)
                  .reduce(
                      (previous, current) =>
                          current
                              ? {
                                    ...previous,
                                    [current.id]: current,
                                }
                              : previous,
                      {},
                  )
            : undefined,
    };
}
