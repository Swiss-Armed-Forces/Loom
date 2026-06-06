import { Box, BoxProps, Skeleton, styled } from "@mui/material";
import { SimpleTreeView } from "@mui/x-tree-view";
import { Dispatch, useEffect, useReducer, useState } from "react";
import { useDispatch } from "react-redux";
import { toast } from "react-toastify";

import { getTreeLevelNodeLimit, searchTree } from "@app/api/index";
import { useAppSelector } from "@app/hooks";
import {
    selectIsLoading,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import { selectQuery } from "@app/slices/searchSlice";
import { AppDispatch } from "@app/store";
import { SearchQuery } from "@features/common/utils/model";
import { EmptySearchResults } from "@features/search/components";

import { FolderViewNode } from "./FolderTreeItem";
import styles from "./FolderView.module.css";
import { folderViewReducer } from "./folderViewReducer";
import {
    FolderTree,
    FolderViewAction,
    FolderViewActionType,
    ROOT_NODE,
} from "./folderViewState";
import { cloneTree, findTreeNode } from "./util";

const FALLBACK_MAX_CHILDREN_COUNT = 100;

const View = styled(Box)<BoxProps>(() => ({
    width: "100%",
    padding: "1rem",
}));

const LoadingIndicator = () => (
    <div className={styles.skeletonLoadingContainer}>
        <Skeleton variant="text" />
        <Skeleton variant="text" />
        <Skeleton variant="text" />
        <Skeleton variant="text" />
    </div>
);

const loadChildren = async (
    parent: FolderTree | null,
    searchQuery: SearchQuery,
    parentPath: string,
    folderDispatch: Dispatch<FolderViewAction>,
    depth = 2,
) => {
    let children;
    if (!parent?.children) {
        folderDispatch({
            type: FolderViewActionType.CHILDREN_LOAD_STARTED,
            parentPath,
        });
        try {
            children = await searchTree(searchQuery, parentPath);
            folderDispatch({
                type: FolderViewActionType.CHILDREN_ADDED,
                children,
                parentPath,
            });
        } finally {
            folderDispatch({
                type: FolderViewActionType.CHILDREN_LOAD_FINISHED,
                parentPath,
            });
        }
    } else {
        children = Object.values(parent.children);
    }

    if (depth > 1) {
        await Promise.all(
            children.map(async (child) => {
                const path = "id" in child ? child.id : child.fullPath;
                if (!path) {
                    return;
                }
                await loadChildren(
                    "id" in child ? child : null,
                    searchQuery,
                    path,
                    folderDispatch,
                    depth - 1,
                );
            }),
        );
    }
};

export const FolderView = () => {
    const searchQuery = useAppSelector(selectQuery);
    const isLoading = useAppSelector(selectIsLoading);
    const dispatch = useDispatch<AppDispatch>();
    const [maxChildren, setMaxChildren] = useState(FALLBACK_MAX_CHILDREN_COUNT);
    const [folderState, folderDispatch] = useReducer(folderViewReducer, {
        tree: cloneTree(ROOT_NODE),
        expandedNodes: [],
    });

    const handleExpandedItemsChange = (
        _: React.SyntheticEvent | null,
        nodeIds: string[],
    ) => {
        folderDispatch({
            type: FolderViewActionType.EXPANDED_NODES_CHANGED,
            expandedNodes: nodeIds,
        });
    };

    const handleItemClick = (path: string) => {
        if (!searchQuery?.query) {
            return;
        }
        const parent = findTreeNode(folderState.tree, path);
        if (!parent) {
            return;
        }

        loadChildren(parent, searchQuery, path, folderDispatch).catch((err) => {
            toast.error(
                "Cannot load tree search results. Error: " +
                    (err["detail"] ? err["detail"] : err),
            );
        });
    };

    useEffect(() => {
        getTreeLevelNodeLimit().then(setMaxChildren);
    }, []);

    useEffect(() => {
        folderDispatch({ type: FolderViewActionType.QUERY_CHANGED });
    }, [searchQuery, searchQuery?.query, folderDispatch]);

    useEffect(() => {
        if (!searchQuery?.query) {
            return;
        }

        // Only need to load the root once
        if (folderState.tree.children || folderState.tree.loading) {
            return;
        }

        dispatch(startLoadingIndicator());
        loadChildren(
            folderState.tree,
            searchQuery,
            ROOT_NODE.id,
            folderDispatch,
            3,
        )
            .catch((err) => {
                toast.error(
                    "Cannot load tree search results. Error: " +
                        (err &&
                        typeof err === "object" &&
                        "detail" in err &&
                        err.detail
                            ? err.detail
                            : err),
                );
                folderDispatch({ type: FolderViewActionType.QUERY_CHANGED });
            })
            .finally(() => {
                dispatch(stopLoadingIndicator());
                folderDispatch({
                    type: FolderViewActionType.INITIAL_DATA_LOADED,
                });
            });
    }, [
        searchQuery,
        searchQuery?.query,
        folderState,
        folderState.tree,
        folderDispatch,
        dispatch,
    ]);

    if (isLoading && !folderState.tree.children) return <LoadingIndicator />;
    if (!Object.keys(folderState.tree.children ?? {}).length)
        return <EmptySearchResults />;

    return (
        <View>
            <div className={styles.treeView}>
                <SimpleTreeView
                    expandedItems={folderState.expandedNodes}
                    onExpandedItemsChange={handleExpandedItemsChange}
                >
                    <FolderViewNode
                        tree={folderState.tree}
                        onClick={handleItemClick}
                        maxChildren={maxChildren}
                    />
                </SimpleTreeView>
            </div>
        </View>
    );
};
