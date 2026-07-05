import {
    ChildrenAddedAction,
    ChildrenLoadFinishedAction,
    ChildrenLoadStartedAction,
    ExpandedNodesChangedAction,
    FolderTree,
    FolderViewAction,
    FolderViewActionType,
    FolderViewState,
    PATH_SEPARATOR,
    ROOT_NODE,
} from "./folderViewState";
import { cloneSpineToPath, cloneTree, findTreeNode } from "./util";
const DEFAULT_EXPANDED_NODES_DEPTH = 2;

const handleQueryChangedAction = (state: FolderViewState): FolderViewState => {
    return { ...state, tree: cloneTree(ROOT_NODE), expandedNodes: [] };
};

const handleChildrenAddedAction = (
    state: FolderViewState,
    action: ChildrenAddedAction,
): FolderViewState => {
    const clonedTree = cloneSpineToPath(state.tree, action.parentPath);
    const currentDirectory = findTreeNode(clonedTree, action.parentPath);
    if (!currentDirectory) return state;

    currentDirectory.children ??= {};
    for (const child of action.children) {
        const path = child.fullPath;
        const fileName = path.split(PATH_SEPARATOR).at(-1);
        currentDirectory.children[path] = {
            // Preserve existing node (especially its loaded children) so that
            // refreshing counts does not collapse already-expanded subtrees.
            ...currentDirectory.children[path],
            id: path,
            label: fileName,
            fileCount: child.fileCount,
            unseenCount: child.unseenCount ?? 0,
            isUnseen: child.isUnseen ?? false,
            flaggedCount: child.flaggedCount ?? 0,
            isFlagged: child.isFlagged ?? false,
            fileId: child.fileId ?? undefined,
        };
    }

    return { ...state, tree: clonedTree };
};

const handleExpandedNodesChangedAction = (
    state: FolderViewState,
    action: ExpandedNodesChangedAction,
): FolderViewState => {
    return { ...state, expandedNodes: [...action.expandedNodes] };
};

const handleInitialDataLoadedAction = (
    state: FolderViewState,
): FolderViewState => {
    const expandedSet = new Set(state.expandedNodes);

    const handleChildren = (
        depth: number,
        nodes: Record<string, FolderTree> | undefined,
    ) => {
        if (!nodes) return;
        for (const node of Object.values(nodes)) {
            if (depth >= DEFAULT_EXPANDED_NODES_DEPTH) return;

            expandedSet.add(node.id);
            handleChildren(depth + 1, node.children);
        }
    };

    expandedSet.add(state.tree.id);
    handleChildren(1, state.tree?.children);
    return { ...state, expandedNodes: [...expandedSet] };
};

const handleChildrenLoadStartedAction = (
    state: FolderViewState,
    action: ChildrenLoadStartedAction,
): FolderViewState => {
    const clonedTree = cloneSpineToPath(state.tree, action.parentPath);
    const parent = findTreeNode(clonedTree, action.parentPath);
    if (parent) parent.loading = true;

    return { ...state, tree: clonedTree };
};

const handleChildrenLoadFinishedAction = (
    state: FolderViewState,
    action: ChildrenLoadFinishedAction,
): FolderViewState => {
    const clonedTree = cloneSpineToPath(state.tree, action.parentPath);
    const parent = findTreeNode(clonedTree, action.parentPath);
    delete parent?.loading;

    return { ...state, tree: clonedTree };
};

export const folderViewReducer = (
    state: FolderViewState,
    action: FolderViewAction,
): FolderViewState => {
    switch (action.type) {
        case FolderViewActionType.CHILDREN_ADDED:
            return handleChildrenAddedAction(state, action);
        case FolderViewActionType.QUERY_CHANGED:
            return handleQueryChangedAction(state);
        case FolderViewActionType.EXPANDED_NODES_CHANGED:
            return handleExpandedNodesChangedAction(state, action);
        case FolderViewActionType.INITIAL_DATA_LOADED:
            return handleInitialDataLoadedAction(state);
        case FolderViewActionType.CHILDREN_LOAD_STARTED:
            return handleChildrenLoadStartedAction(state, action);
        case FolderViewActionType.CHILDREN_LOAD_FINISHED:
            return handleChildrenLoadFinishedAction(state, action);
        default:
            return state;
    }
};
