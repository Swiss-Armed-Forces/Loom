import { TreeNodeModel } from "@app/api";

export const PATH_ROOT_NAME = "/";
export const PATH_SEPARATOR = "/";
export const ROOT_NODE: FolderTree = {
    id: PATH_ROOT_NAME,
    label: PATH_ROOT_NAME + PATH_SEPARATOR,
};

export interface FolderTree {
    id: string;
    label: React.ReactNode;
    fileCount?: number;
    unseenCount?: number;
    isUnseen?: boolean;
    flaggedCount?: number;
    isFlagged?: boolean;
    fileId?: string;
    children?: Record<string, FolderTree>;
    loading?: boolean;
}

export interface FolderViewState {
    tree: FolderTree;
    expandedNodes: string[];
}

export const FolderViewActionType = {
    EXPANDED_NODES_CHANGED: "expandedNodesChanged",
    CHILDREN_ADDED: "childrenAdded",
    QUERY_CHANGED: "queryChanged",
    INITIAL_DATA_LOADED: "initialDataLoaded",
    CHILDREN_LOAD_STARTED: "childrenLoadStarted",
    CHILDREN_LOAD_FINISHED: "childrenLoadFinished",
} as const;
export type FolderViewActionType =
    (typeof FolderViewActionType)[keyof typeof FolderViewActionType];

interface BaseFolderViewAction<TYPE extends FolderViewActionType> {
    type: TYPE;
}

export interface ChildrenAddedAction extends BaseFolderViewAction<
    typeof FolderViewActionType.CHILDREN_ADDED
> {
    children: TreeNodeModel[];
    parentPath: string;
}

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface QueryChangedAction extends BaseFolderViewAction<
    typeof FolderViewActionType.QUERY_CHANGED
> {}

export interface ExpandedNodesChangedAction extends BaseFolderViewAction<
    typeof FolderViewActionType.EXPANDED_NODES_CHANGED
> {
    expandedNodes: string[];
}

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface InitialDataLoadedAction extends BaseFolderViewAction<
    typeof FolderViewActionType.INITIAL_DATA_LOADED
> {}

export interface ChildrenLoadStartedAction extends BaseFolderViewAction<
    typeof FolderViewActionType.CHILDREN_LOAD_STARTED
> {
    parentPath: string;
}

export interface ChildrenLoadFinishedAction extends BaseFolderViewAction<
    typeof FolderViewActionType.CHILDREN_LOAD_FINISHED
> {
    parentPath: string;
}
export type FolderViewAction =
    | ChildrenAddedAction
    | QueryChangedAction
    | ExpandedNodesChangedAction
    | InitialDataLoadedAction
    | ChildrenLoadStartedAction
    | ChildrenLoadFinishedAction;
