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
    SpineNodesMergedAction,
} from "./folderViewState";
import { cloneSpineToPath, cloneTree, findTreeNode } from "./util";
const DEFAULT_EXPANDED_NODES_DEPTH = 2;

const handleQueryChangedAction = (state: FolderViewState): FolderViewState => {
    return {
        ...state,
        tree: cloneTree(ROOT_NODE),
        expandedNodes: [],
        fileIds: new Set(),
    };
};

const handleChildrenAddedAction = (
    state: FolderViewState,
    action: ChildrenAddedAction,
): FolderViewState => {
    const clonedTree = cloneSpineToPath(state.tree, action.parentPath);
    const currentDirectory = findTreeNode(clonedTree, action.parentPath);
    if (!currentDirectory) return state;

    currentDirectory.children ??= {};
    const newFileIds = new Set(state.fileIds);
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
        if (child.fileId) newFileIds.add(child.fileId);
    }
    // Only update nextPageCursor when the action explicitly carries one (not
    // undefined). undefined means "this dispatch is not a pagination request"
    // (e.g. a count-refresh from reloadAncestors), so the existing cursor is
    // preserved. null means the last page has been fetched.
    if (action.nextPageCursor !== undefined) {
        currentDirectory.nextPageCursor = action.nextPageCursor;
    }

    return { ...state, tree: clonedTree, fileIds: newFileIds };
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
            // Only auto-expand nodes whose children have already been loaded.
            // Expanding a node with unloaded children would show a down arrow
            // with no visible content until the user manually triggers a fetch.
            if (!node.children) continue;

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

const handleSpineNodesMergedAction = (
    state: FolderViewState,
    action: SpineNodesMergedAction,
): FolderViewState => {
    if (action.nodes.length === 0) return state;

    let clonedTree = state.tree;
    const newFileIds = new Set(state.fileIds);
    for (let i = 0; i < action.nodes.length; i++) {
        const node = action.nodes[i];
        const parentPath =
            i === 0 ? ROOT_NODE.id : String(action.nodes[i - 1].fullPath);

        clonedTree = cloneSpineToPath(clonedTree, parentPath);
        const parent = findTreeNode(clonedTree, parentPath);
        if (!parent) continue;

        const path = String(node.fullPath);
        const label = path.split(PATH_SEPARATOR).at(-1);

        parent.children ??= {};
        parent.children[path] = {
            ...parent.children[path],
            id: path,
            label,
            fileCount: node.fileCount,
            unseenCount: node.unseenCount ?? 0,
            isUnseen: node.isUnseen ?? false,
            flaggedCount: node.flaggedCount ?? 0,
            isFlagged: node.isFlagged ?? false,
            fileId: node.fileId ?? undefined,
        };
        if (node.fileId) newFileIds.add(node.fileId);
    }
    return { ...state, tree: clonedTree, fileIds: newFileIds };
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
        case FolderViewActionType.SPINE_NODES_MERGED:
            return handleSpineNodesMergedAction(state, action);
        default:
            return state;
    }
};
