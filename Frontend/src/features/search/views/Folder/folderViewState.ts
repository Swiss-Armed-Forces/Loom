import { TreeNodeModel } from "@app/api";

export const PATH_ROOT_NAME = "/";
export const PATH_SEPARATOR = "/";
export const ROOT_NODE: FolderTree = {
    id: PATH_ROOT_NAME,
    label: PATH_ROOT_NAME + PATH_SEPARATOR,
};

/** Edge length of a file's type avatar in a folder-panel row, in pixels.
 *  Shared by the tree and the flat filter list, which are the same row height. */
export const ROW_AVATAR_SIZE_PX = 17;

/** Which of the two mounted folder views a piece of state belongs to.
 *
 *  Expansion is already stored per panel under this key, and the depth limits
 *  follow it rather than inventing a second discriminator. */
export type FolderViewExpansionKey = "global" | "filtered";

export interface FolderTree {
    id: string;
    label: React.ReactNode;
    fileCount?: number;
    unseenCount?: number;
    isUnseen?: boolean;
    flaggedCount?: number;
    isFlagged?: boolean;
    directChildrenCount?: number;
    fileId?: string;
    /** MIME type and group of the file at this node, for its type icon. Set on
     *  leaf nodes only — a directory has no type of its own. */
    mimeType?: string;
    mimeTypeGroup?: string;
    children?: Record<string, FolderTree>;
    loading?: boolean;
    /**
     * Cursor for fetching the next backend page of children.
     * undefined = not yet fetched; string = cursor available; null = all pages loaded.
     */
    nextPageCursor?: string | null;
}

export interface FolderViewState {
    tree: FolderTree;
    expandedNodes: string[];
    fileIds: Set<string>;
}

export const FolderViewActionType = {
    EXPANDED_NODES_CHANGED: "expandedNodesChanged",
    CHILDREN_ADDED: "childrenAdded",
    QUERY_CHANGED: "queryChanged",
    INITIAL_DATA_LOADED: "initialDataLoaded",
    CHILDREN_LOAD_STARTED: "childrenLoadStarted",
    CHILDREN_LOAD_FINISHED: "childrenLoadFinished",
    SPINE_NODES_MERGED: "spineNodesMerged",
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
    nextPageCursor?: string | null;
    /** Root node aggregate stats from the backend; only set when parentPath is the root. */
    rootStats?: TreeNodeModel;
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

export interface SpineNodesMergedAction extends BaseFolderViewAction<
    typeof FolderViewActionType.SPINE_NODES_MERGED
> {
    nodes: TreeNodeModel[]; // ordered root → leaf
    /** Root node aggregate stats from the backend. */
    rootStats?: TreeNodeModel;
}

export type FolderViewAction =
    | ChildrenAddedAction
    | QueryChangedAction
    | ExpandedNodesChangedAction
    | InitialDataLoadedAction
    | ChildrenLoadStartedAction
    | ChildrenLoadFinishedAction
    | SpineNodesMergedAction;
