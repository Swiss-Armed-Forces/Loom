import { TreeNodeModel } from "../../../../app/api";

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
    children?: Record<string, FolderTree>;
    loading?: boolean;
}

export interface FolderViewState {
    tree: FolderTree;
    expandedNodes: string[];
}

export const enum FolderViewActionType {
    EXPANDED_NODES_CHANGED = "expandedNodesChanged",
    CHILDREN_ADDED = "childrenAdded",
    QUERY_CHANGED = "queryChanged",
    INITIAL_DATA_LOADED = "initialDataLoaded",
    CHILDREN_LOAD_STARTED = "childrenLoadStarted",
    CHILDREN_LOAD_FINISHED = "childrenLoadFinished",
}

interface BaseFolderViewAction<TYPE extends FolderViewActionType> {
    type: TYPE;
}

export interface ChildrenAddedAction
    extends BaseFolderViewAction<FolderViewActionType.CHILDREN_ADDED> {
    children: TreeNodeModel[];
    parentPath: string;
}

export interface QueryChangedAction
    extends BaseFolderViewAction<FolderViewActionType.QUERY_CHANGED> {}

export interface ExpandedNodesChangedAction
    extends BaseFolderViewAction<FolderViewActionType.EXPANDED_NODES_CHANGED> {
    expandedNodes: string[];
}

export interface InitialDataLoadedAction
    extends BaseFolderViewAction<FolderViewActionType.INITIAL_DATA_LOADED> {}

export interface ChildrenLoadStartedAction
    extends BaseFolderViewAction<FolderViewActionType.CHILDREN_LOAD_STARTED> {
    parentPath: string;
}

export interface ChildrenLoadFinishedAction
    extends BaseFolderViewAction<FolderViewActionType.CHILDREN_LOAD_FINISHED> {
    parentPath: string;
}
export type FolderViewAction =
    | ChildrenAddedAction
    | QueryChangedAction
    | ExpandedNodesChangedAction
    | InitialDataLoadedAction
    | ChildrenLoadStartedAction
    | ChildrenLoadFinishedAction;
