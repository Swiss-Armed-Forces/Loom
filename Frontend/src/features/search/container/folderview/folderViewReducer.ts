import {
    ChildrenAddedAction,
    ChildrenLoadFinishedAction,
    ChildrenLoadStartedAction,
    ExpandedNodesChangedAction,
    FolderTree,
    FolderViewAction,
    FolderViewActionType,
    FolderViewState,
    PATH_ROOT_NAME,
    PATH_SEPARATOR,
    ROOT_NODE,
} from "./folderViewState";
import { cloneTree, findTreeNode } from "./util";
const DEFAULT_EXPANDED_NODES_DEPTH = 2;

function handleQueryChangedAction(state: FolderViewState): FolderViewState {
    return { ...state, tree: cloneTree(ROOT_NODE), expandedNodes: [] };
}

function handleChildrenAddedAction(
    state: FolderViewState,
    action: ChildrenAddedAction,
): FolderViewState {
    const directories = action.parentPath
        .split(PATH_SEPARATOR)
        .filter((v) => !!v);

    const clonedTree = cloneTree(state.tree);
    let currentDirectory = clonedTree;
    let currentPartialPath = PATH_ROOT_NAME;
    for (const dirPath of directories) {
        let subDir = findTreeNode(currentDirectory, dirPath);
        currentPartialPath += `${PATH_SEPARATOR}${dirPath}`;

        if (!subDir) {
            currentDirectory.children ??= {};
            subDir = currentDirectory.children[currentPartialPath] = {
                ...currentDirectory.children[currentPartialPath],
                [currentPartialPath]: {
                    id: currentPartialPath,
                    label: dirPath,
                },
            } as FolderTree;
        }
        currentDirectory = subDir;
    }

    currentDirectory.children ??= {};
    for (const child of action.children) {
        const path = child.fullPath!;
        const fileName = path.split(PATH_SEPARATOR).at(-1);
        currentDirectory.children[path] = {
            id: path,
            label: fileName,
            fileCount: child.fileCount,
        };
    }

    return { ...state, tree: clonedTree };
}

function handleExpandedNodesChangedAction(
    state: FolderViewState,
    action: ExpandedNodesChangedAction,
): FolderViewState {
    return { ...state, expandedNodes: [...action.expandedNodes] };
}

function handleInitialDataLoadedAction(
    state: FolderViewState,
): FolderViewState {
    const expandedNodes = [...state.expandedNodes];

    function handleChildren(
        depth: number,
        nodes: Record<string, FolderTree> | undefined,
    ) {
        if (!nodes) return;
        for (const node of Object.values(nodes)) {
            if (depth >= DEFAULT_EXPANDED_NODES_DEPTH) return;

            if (!expandedNodes.includes(node.id)) expandedNodes.push(node.id);
            handleChildren(depth + 1, node.children);
        }
    }

    if (!expandedNodes.includes(state.tree.id))
        expandedNodes.push(state.tree.id);
    handleChildren(1, state.tree?.children);
    return { ...state, expandedNodes };
}

function handleChildrenLoadStartedAction(
    state: FolderViewState,
    action: ChildrenLoadStartedAction,
): FolderViewState {
    const clonedTree = cloneTree(state.tree);
    const parent = findTreeNode(clonedTree, action.parentPath);
    if (parent) parent.loading = true;

    return { ...state, tree: clonedTree };
}

function handleChildrenLoadFinishedAction(
    state: FolderViewState,
    action: ChildrenLoadFinishedAction,
): FolderViewState {
    const clonedTree = cloneTree(state.tree);
    const parent = findTreeNode(clonedTree, action.parentPath);
    delete parent?.loading;

    return { ...state, tree: clonedTree };
}

export function folderViewReducer(
    state: FolderViewState,
    action: FolderViewAction,
): FolderViewState {
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
    }
}
