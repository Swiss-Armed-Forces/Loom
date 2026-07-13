import { MoreHoriz } from "@mui/icons-material";
import {
    Box,
    BoxProps,
    CircularProgress,
    List,
    ListItemButton,
    ListItemText,
    Skeleton,
    Stack,
    Typography,
    styled,
} from "@mui/material";
import { SimpleTreeView, useSimpleTreeViewApiRef } from "@mui/x-tree-view";
import {
    Dispatch,
    useCallback,
    useEffect,
    useReducer,
    useRef,
    useState,
} from "react";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";
import { toast } from "react-toastify";

import type { TreeNodeModel } from "@app/api/index";
import { getTreeSpine, searchByFilename, searchTree } from "@app/api/index";
import {
    subscribeChannel,
    unsubscribeChannel,
} from "@app/channelSubscriptions";
import { useAppSelector } from "@app/hooks";
import {
    selectIsLoading,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import {
    fetchPreview,
    selectActiveTabFileId,
    selectFiles,
    selectHighlightedFileId,
    selectQuery,
    selectWebSocketPubSubMessage,
    setActiveTabFileId,
    setFolderViewExpandedNodes,
    setHighlightedFileId,
    setTemporaryFileId,
} from "@app/slices/searchSlice";
import { AppDispatch, store } from "@app/store";
import { SearchQuery } from "@features/common/utils/model";

import {
    FolderViewNode,
    NodeAddToQueryButton,
    NodeCountBadges,
    NodeViewDetailsButton,
} from "./FolderTreeItem";
import styles from "./FolderView.module.css";
import { folderViewReducer } from "./folderViewReducer";
import {
    FolderTree,
    FolderViewAction,
    FolderViewActionType,
    ROOT_NODE,
    PATH_SEPARATOR,
} from "./folderViewState";
import {
    cloneTree,
    findAncestorNodeIds,
    findNodeByFileId,
    findTreeNode,
} from "./util";

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
    let childNodes: FolderTree[];
    if (!parent?.children) {
        folderDispatch({
            type: FolderViewActionType.CHILDREN_LOAD_STARTED,
            parentPath,
        });
        try {
            const result = await searchTree(
                { ...searchQuery, id: null },
                parentPath,
            );
            folderDispatch({
                type: FolderViewActionType.CHILDREN_ADDED,
                children: result.nodes,
                parentPath,
                nextPageCursor: result.nextPageCursor ?? null,
            });
            childNodes = result.nodes.map((node) => ({
                id: node.fullPath,
                label: node.fullPath.split(PATH_SEPARATOR).at(-1),
            }));
        } finally {
            folderDispatch({
                type: FolderViewActionType.CHILDREN_LOAD_FINISHED,
                parentPath,
            });
        }
    } else {
        childNodes = Object.values(parent.children);
    }

    if (depth > 1) {
        await Promise.all(
            childNodes.map(async (child) => {
                await loadChildren(
                    child,
                    searchQuery,
                    child.id,
                    folderDispatch,
                    depth - 1,
                );
            }),
        );
    }
};

interface FolderViewProps {
    filter?: string;
}

export const FolderView = ({ filter }: FolderViewProps) => {
    const { t } = useTranslation();
    const searchQuery = useAppSelector(selectQuery);
    const isLoading = useAppSelector(selectIsLoading);
    const activeTabFileId = useAppSelector(selectActiveTabFileId);
    const highlightedFileId = useAppSelector(selectHighlightedFileId);
    const focusedFileId = activeTabFileId ?? highlightedFileId;
    const files = useAppSelector(selectFiles);
    const focusedFilePath = focusedFileId
        ? (files[focusedFileId]?.preview?.path ?? null)
        : null;

    const webSocketPubSubMessage = useAppSelector(selectWebSocketPubSubMessage);

    const dispatch = useDispatch<AppDispatch>();
    const treeApiRef = useSimpleTreeViewApiRef();
    const [folderState, folderDispatch] = useReducer(folderViewReducer, {
        tree: cloneTree(ROOT_NODE),
        expandedNodes: [],
        fileIds: new Set<string>(),
    });
    const folderStateRef = useRef(folderState);
    folderStateRef.current = folderState;
    const searchQueryRef = useRef(searchQuery);
    searchQueryRef.current = searchQuery;
    // Tracks only nodes the user explicitly expanded/collapsed. Auto-expanded
    // ancestors (from card/tab navigation) are not stored here so they are
    // discarded when the focused file changes.
    // Initialised from the Redux-persisted value so expansion survives
    // sidebar panel switches and page reloads.
    const [userExpandedNodes, setUserExpandedNodes] = useState<string[]>(
        () => store.getState().search.folderViewExpandedNodes,
    );
    const userExpandedNodesRef = useRef(userExpandedNodes);
    userExpandedNodesRef.current = userExpandedNodes;
    // Query seen on the previous render. Tracks both id and query string so we
    // can distinguish a genuine new search from a pure ID-only change (keep-alive
    // renewal, React strict-mode double-mount) that carries the same results.
    const prevQueryRef = useRef<string | undefined>(searchQuery?.id);
    // Whether the initial auto-expand has been synced into userExpandedNodes.
    // After the first tree load, initial auto-expanded nodes are promoted into
    // the user snapshot so that WebSocket refreshes (which re-trigger the
    // auto-expand effect) never collapse them.
    const initialExpandSynced = useRef(false);
    // Tracks the last focusedFileId that was successfully scrolled into view.
    // Prevents re-scrolling on every expand/collapse when the highlight hasn't changed.
    const lastScrolledFileId = useRef<string | null>(null);
    // Tracks which fileIds the FolderView has subscribed to for WS updates so
    // that we can diff on tree changes and unsubscribe cleanly on reset.
    const subscribedTreeFileIds = useRef(new Set<string>());
    const filesRef = useRef(files);
    filesRef.current = files;

    useEffect(() => {
        if (initialExpandSynced.current) return;
        if (folderState.expandedNodes.length === 0) return;

        initialExpandSynced.current = true;

        // Merge auto-expanded nodes with any nodes restored from localStorage so
        // that the persisted expansion is not overwritten by the initial auto-expand.
        const merged = Array.from(
            new Set([...userExpandedNodes, ...folderState.expandedNodes]),
        );
        setUserExpandedNodes(merged);
        folderDispatch({
            type: FolderViewActionType.EXPANDED_NODES_CHANGED,
            expandedNodes: merged,
        });
    }, [folderState.expandedNodes, userExpandedNodes, folderDispatch]);

    // After the initial-expand sync, cascade-load children for any expanded
    // node that is in the tree but hasn't had its children fetched yet.
    // Re-runs each time the tree or expandedNodes changes so deeper levels are
    // loaded progressively as each parent's CHILDREN_ADDED action arrives,
    // restoring the full multi-level expansion state after F5.
    useEffect(() => {
        if (!initialExpandSynced.current || !searchQueryRef.current) return;
        folderState.expandedNodes.forEach((nodeId) => {
            const node = findTreeNode(folderState.tree, nodeId);
            if (node && !node.children && !node.loading) {
                loadChildren(
                    node,
                    searchQueryRef.current!,
                    nodeId,
                    folderDispatch,
                    1,
                ).catch(() => {});
            }
        });
    }, [folderState.tree, folderState.expandedNodes, folderDispatch]);

    // Persist user-driven expansion to Redux (→ localStorage via middleware)
    // so the state survives sidebar panel switches and page reloads.
    useEffect(() => {
        dispatch(setFolderViewExpandedNodes(userExpandedNodes));
    }, [userExpandedNodes, dispatch]);

    // Maintain WS subscriptions for all file nodes currently loaded in the
    // tree. This ensures fileUpdate messages arrive even when those files are
    // not visible as result cards and no detail tab is open for them.
    useEffect(() => {
        const currentFileIds = folderState.fileIds;
        const subscribedIds = subscribedTreeFileIds.current;

        currentFileIds.forEach((fileId) => {
            if (!subscribedIds.has(fileId)) {
                subscribeChannel(fileId, dispatch);
                subscribedIds.add(fileId);
            }
        });

        subscribedIds.forEach((fileId) => {
            if (!currentFileIds.has(fileId)) {
                unsubscribeChannel(fileId, dispatch);
                subscribedIds.delete(fileId);
            }
        });
    }, [folderState.fileIds, dispatch]);

    // Unsubscribe all channels on unmount only and reset the initial-expand flag
    // so that when the component remounts (e.g. user switches panel and back)
    // the localStorage-restoration sync runs again.
    useEffect(() => {
        const subscribedIds = subscribedTreeFileIds.current;
        return () => {
            subscribedIds.forEach((fileId) =>
                unsubscribeChannel(fileId, dispatch),
            );
            subscribedIds.clear();
            initialExpandSynced.current = false;
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const handleExpandedItemsChange = (
        _: React.SyntheticEvent | null,
        nodeIds: string[],
    ) => {
        // Compute what the user toggled by diffing against the current display
        // state, then apply only that delta to the user snapshot.
        const collapsed = folderState.expandedNodes.filter(
            (id) => !nodeIds.includes(id),
        );
        const added = nodeIds.filter(
            (id) => !folderState.expandedNodes.includes(id),
        );
        setUserExpandedNodes((prev) => {
            if (added.length > 0) return [...prev, ...added];
            if (collapsed.length > 0)
                return prev.filter((id) => !collapsed.includes(id));
            return prev;
        });
        folderDispatch({
            type: FolderViewActionType.EXPANDED_NODES_CHANGED,
            expandedNodes: nodeIds,
        });

        // Load children for newly expanded nodes that have not been fetched yet.
        // This handles the case where the user clicks the expand arrow directly
        // (which fires this handler but not onItemClick).
        if (searchQueryRef.current) {
            added.forEach((id) => {
                const node = findTreeNode(folderStateRef.current.tree, id);
                if (node && !node.children && !node.loading) {
                    loadChildren(
                        node,
                        searchQueryRef.current!,
                        id,
                        folderDispatch,
                        1,
                    ).catch((err) => {
                        toast.error(
                            "Cannot load tree search results. Error: " +
                                (err &&
                                typeof err === "object" &&
                                "detail" in err &&
                                err.detail
                                    ? err.detail
                                    : err),
                        );
                    });
                }
            });
        }
    };

    const handleFileClick = useCallback(
        (fileId: string) => {
            dispatch(setActiveTabFileId(null));
            if (!files[fileId]?.meta) {
                // File not in current results — show as temporary card.
                dispatch(setTemporaryFileId(fileId));
                dispatch(fetchPreview({ fileId }));
            }
            dispatch(setHighlightedFileId(fileId));
        },
        [files, dispatch],
    );

    const handleItemClick = (path: string) => {
        const node = findTreeNode(folderState.tree, path);
        if (!node) return;

        // If this node has a fileId, navigate to it in the results panel
        if (node.fileId) {
            handleFileClick(node.fileId);
        }
    };

    // Refresh the given file and all its ancestors in the tree using the spine
    // endpoint, which returns the file node plus every ancestor directory with
    // up-to-date counts in a single round-trip. This works regardless of which
    // pagination page the file or any ancestor directory is on.
    // Returns a cleanup function that cancels any in-flight dispatch.
    // Reads tree and searchQuery via refs so the callback identity is stable.
    const reloadAncestors = useCallback(
        (fileId: string) => {
            const searchQuery = searchQueryRef.current;
            if (!searchQuery) return undefined;

            // Resolve the file's full path — from the in-memory tree first,
            // then fall back to the Redux preview store (set when a detail tab
            // has been opened for the file).
            const filePath =
                findNodeByFileId(folderStateRef.current.tree, fileId)?.id ??
                filesRef.current[fileId]?.preview?.path;

            if (!filePath) return undefined;

            let cancelled = false;
            void getTreeSpine({ ...searchQuery, id: null }, filePath)
                .then((result) => {
                    if (cancelled || result.nodes.length === 0) return;
                    folderDispatch({
                        type: FolderViewActionType.SPINE_NODES_MERGED,
                        nodes: result.nodes,
                    });
                })
                .catch((err) => {
                    if (cancelled) return;
                    toast.error(
                        "Cannot refresh folder tree after file update. Error: " +
                            (err &&
                            typeof err === "object" &&
                            "detail" in err &&
                            err.detail
                                ? err.detail
                                : err),
                    );
                });
            return () => {
                cancelled = true;
            };
        },
        [folderDispatch],
    );

    // On fileUpdate, reload ancestor paths of the changed file so counts stay fresh.
    // FolderView subscribes to all tree fileIds above, so the message arrives
    // regardless of whether the result card is in view or a tab is open.
    useEffect(() => {
        if (!webSocketPubSubMessage) return;
        const msg = webSocketPubSubMessage.message;
        if (msg.type !== "fileUpdate") return;
        const { fileId } = msg as { type: string; fileId: string };
        return reloadAncestors(fileId);
    }, [webSocketPubSubMessage, reloadAncestors]);

    useEffect(() => {
        if (!focusedFileId || !searchQuery) return;

        // If the node is already in the tree, expand all its ancestors.
        // Use ref to avoid re-running on every tree update — the effect only
        // needs to re-run when focusedFileId, focusedFilePath, or searchQuery change.
        const ancestors = findAncestorNodeIds(
            folderStateRef.current.tree,
            focusedFileId,
        );
        if (ancestors !== null) {
            const newExpanded = Array.from(
                new Set([...userExpandedNodesRef.current, ...ancestors]),
            );
            folderDispatch({
                type: FolderViewActionType.EXPANDED_NODES_CHANGED,
                expandedNodes: newExpanded,
            });
            return;
        }

        // Node not yet in tree — call the spine endpoint to get all ancestor
        // nodes in one round-trip, then eagerly load full siblings for each
        // ancestor in parallel so the user sees complete folder contents.
        if (!focusedFilePath) return;

        getTreeSpine(searchQuery, focusedFilePath)
            .then((result) => {
                if (result.nodes.length === 0) return;
                folderDispatch({
                    type: FolderViewActionType.SPINE_NODES_MERGED,
                    nodes: result.nodes,
                });
                // Expand all ancestors (spine nodes excluding the leaf file).
                const ancestorPaths = result.nodes
                    .slice(0, -1)
                    .map((n) => String(n.fullPath));
                folderDispatch({
                    type: FolderViewActionType.EXPANDED_NODES_CHANGED,
                    expandedNodes: Array.from(
                        new Set([
                            ...userExpandedNodesRef.current,
                            ...ancestorPaths,
                        ]),
                    ),
                });
                // Eagerly load full siblings for each spine ancestor so the
                // user sees complete folder contents, not a sparse skeleton.
                ancestorPaths.forEach((path) => {
                    searchTree({ ...searchQuery, id: null }, path)
                        .then((children) => {
                            folderDispatch({
                                type: FolderViewActionType.CHILDREN_ADDED,
                                children: children.nodes,
                                parentPath: path,
                                nextPageCursor: children.nextPageCursor ?? null,
                            });
                        })
                        .catch(() => {
                            // Non-fatal: spine path is already visible.
                        });
                });
            })
            .catch(() => toast.error("Cannot locate file in folder tree."));
    }, [focusedFileId, focusedFilePath, searchQuery]);

    useEffect(() => {
        const prevId = prevQueryRef.current;
        prevQueryRef.current = searchQuery?.id;

        // Skip on the initial render and when the first query loads from the
        // URL so the restored expansion from localStorage is not cleared.
        // Only reset when the search query changes from one known ID to another.
        if (searchQuery?.id === prevId || prevId === undefined) return;

        folderDispatch({ type: FolderViewActionType.QUERY_CHANGED });
        initialExpandSynced.current = false;
        subscribedTreeFileIds.current.forEach((fileId) =>
            unsubscribeChannel(fileId, dispatch),
        );
        subscribedTreeFileIds.current.clear();
    }, [searchQuery?.id, folderDispatch, dispatch]);

    const handleLoadMore = useCallback(
        async (nodeId: string) => {
            const node = findTreeNode(folderStateRef.current.tree, nodeId);
            if (!node?.nextPageCursor || !searchQueryRef.current) return;
            try {
                const result = await searchTree(
                    { ...searchQueryRef.current, id: null },
                    nodeId,
                    node.nextPageCursor,
                );
                folderDispatch({
                    type: FolderViewActionType.CHILDREN_ADDED,
                    children: result.nodes,
                    parentPath: nodeId,
                    nextPageCursor: result.nextPageCursor ?? null,
                });
            } catch (err) {
                toast.error(
                    "Cannot load more folder items. Error: " +
                        (err &&
                        typeof err === "object" &&
                        "detail" in err &&
                        (err as { detail: unknown }).detail
                            ? (err as { detail: unknown }).detail
                            : err),
                );
            }
        },
        [folderDispatch],
    );

    // Scroll the highlighted file's tree node into view when the highlight changes.
    // Keeps `folderState.expandedNodes` in deps so it retries after auto-expansion
    // makes the DOM element available, but the ref guard prevents re-scrolling on
    // manual expand/collapse when the highlighted file has not changed.
    // The 300 ms delay matches MUI's tree expansion animation so we scroll to
    // the element's final position rather than its mid-animation position.
    useEffect(() => {
        if (!focusedFilePath || !treeApiRef.current) return;
        if (focusedFileId === lastScrolledFileId.current) return;
        const id = setTimeout(() => {
            const element =
                treeApiRef.current?.getItemDOMElement(focusedFilePath);
            if (element) {
                element.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest",
                });
                lastScrolledFileId.current = focusedFileId ?? null;
            }
        }, 300);
        return () => clearTimeout(id);
    }, [focusedFileId, focusedFilePath, folderState.expandedNodes, treeApiRef]);

    useEffect(() => {
        if (!searchQuery?.query?.trim()) {
            // Mirror the stats view guard: clear the tree when the query is
            // empty. Only dispatch if the tree still has data to avoid a loop
            // (after QUERY_CHANGED, children is undefined so we skip).
            if (folderState.tree.children !== undefined) {
                folderDispatch({ type: FolderViewActionType.QUERY_CHANGED });
            }
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
            1,
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
        folderDispatch,
        dispatch,
    ]);

    const [filterResults, setFilterResults] = useState<TreeNodeModel[]>([]);
    const [filterLoading, setFilterLoading] = useState(false);
    const [filterLoadingMore, setFilterLoadingMore] = useState(false);
    const [filterNextPageCursor, setFilterNextPageCursor] = useState<
        string | null
    >(null);

    useEffect(() => {
        if (!filter || !searchQuery) {
            setFilterResults([]);
            setFilterNextPageCursor(null);
            return;
        }
        const timer = setTimeout(() => {
            setFilterLoading(true);
            searchByFilename(searchQuery, filter)
                .then((result) => {
                    setFilterNextPageCursor(result.nextPageCursor ?? null);
                    setFilterResults(
                        result.nodes.filter((n) => n.fileId !== undefined),
                    );
                })
                .catch(() => toast.error("Cannot load filter results."))
                .finally(() => setFilterLoading(false));
        }, 300);
        return () => clearTimeout(timer);
    }, [filter, searchQuery]);

    const handleFilterLoadMore = useCallback(() => {
        if (!filterNextPageCursor || !searchQuery || !filter) return;
        setFilterLoadingMore(true);
        searchByFilename(searchQuery, filter, filterNextPageCursor)
            .then((result) => {
                setFilterNextPageCursor(result.nextPageCursor ?? null);
                setFilterResults((prev) => [
                    ...prev,
                    ...result.nodes.filter((n) => n.fileId !== undefined),
                ]);
            })
            .catch(() => toast.error("Cannot load more filter results."))
            .finally(() => setFilterLoadingMore(false));
    }, [filterNextPageCursor, searchQuery, filter]);

    if (isLoading && !folderState.tree.children) return <LoadingIndicator />;
    if (!Object.keys(folderState.tree.children ?? {}).length) return null;

    if (filter) {
        if (filterLoading) return <LoadingIndicator />;
        if (filterResults.length === 0) return null;
        return (
            <>
                <List dense disablePadding>
                    {filterResults.map((node) => {
                        const label =
                            node.fullPath.split(PATH_SEPARATOR).at(-1) ??
                            node.fullPath;
                        const fileId = node.fileId;
                        return (
                            <ListItemButton
                                key={node.fullPath}
                                onClick={() => {
                                    if (!fileId) return;
                                    handleFileClick(fileId);
                                }}
                                title={node.fullPath}
                                selected={fileId === focusedFileId}
                                sx={{
                                    pr: 0.5,
                                    "&.Mui-selected": {
                                        borderLeft: "2px solid",
                                        borderColor: "primary.main",
                                        borderRadius: "0 4px 4px 0",
                                        bgcolor: "primary.main",
                                        color: "primary.contrastText",
                                    },
                                    "&.Mui-selected:hover": {
                                        bgcolor: "primary.dark",
                                    },
                                }}
                            >
                                <ListItemText
                                    primary={
                                        <Stack
                                            direction="row"
                                            spacing={0.5}
                                            sx={{ alignItems: "center" }}
                                        >
                                            <Typography
                                                noWrap
                                                variant="body2"
                                                component="span"
                                                sx={{
                                                    ...(node.isUnseen && {
                                                        fontWeight: "bold",
                                                    }),
                                                    ...(node.isFlagged && {
                                                        color: "error.main",
                                                    }),
                                                }}
                                            >
                                                {label}
                                            </Typography>
                                            <NodeCountBadges
                                                flaggedCount={node.flaggedCount}
                                                unseenCount={node.unseenCount}
                                                fileCount={node.fileCount}
                                            />
                                        </Stack>
                                    }
                                    secondary={node.fullPath}
                                    slotProps={{
                                        primary: { component: "div" },
                                        secondary: {
                                            noWrap: true,
                                            sx: { fontSize: "0.65rem" },
                                        },
                                    }}
                                />
                                <NodeViewDetailsButton fileId={fileId!} />
                                <NodeAddToQueryButton path={node.fullPath} />
                            </ListItemButton>
                        );
                    })}
                </List>
                {filterNextPageCursor && (
                    <ListItemButton
                        onClick={handleFilterLoadMore}
                        disabled={filterLoadingMore}
                        dense
                    >
                        <Stack
                            direction="row"
                            spacing={0.5}
                            sx={{ alignItems: "center", opacity: 0.7 }}
                        >
                            {filterLoadingMore ? (
                                <CircularProgress size="0.9rem" />
                            ) : (
                                <MoreHoriz sx={{ fontSize: "0.9rem" }} />
                            )}
                            <Typography
                                variant="caption"
                                sx={{ fontStyle: "italic" }}
                            >
                                {t("folderView.loadMore")}
                            </Typography>
                        </Stack>
                    </ListItemButton>
                )}
            </>
        );
    }

    return (
        <View>
            <div className={styles.treeView}>
                <SimpleTreeView
                    apiRef={treeApiRef}
                    expandedItems={folderState.expandedNodes}
                    onExpandedItemsChange={handleExpandedItemsChange}
                    expansionTrigger="iconContainer"
                    onItemClick={(event, itemId) => {
                        const target = event.target as HTMLElement;
                        if (target.closest(".MuiTreeItem-iconContainer"))
                            return;
                        handleItemClick(itemId);
                    }}
                    sx={{
                        "& .MuiTreeItem-iconContainer": {
                            borderRadius: "50%",
                            transition:
                                "transform 0.2s ease, opacity 0.2s ease",
                            "&:hover": {
                                bgcolor: "action.hover",
                                transform: "scale(1.1)",
                                opacity: 0.8,
                            },
                        },
                        "& .MuiTreeItem-groupTransition": {
                            position: "relative",
                            "&::before": {
                                content: '""',
                                position: "absolute",
                                left: "calc(8px + var(--TreeView-itemChildrenIndentation, 12px) * var(--TreeView-itemDepth, 0))",
                                top: 0,
                                bottom: 0,
                                borderLeft: "1px solid",
                                borderColor: "divider",
                                pointerEvents: "none",
                                zIndex: 1,
                            },
                        },
                    }}
                >
                    <FolderViewNode
                        tree={folderState.tree}
                        activeTabFileId={focusedFileId}
                        onLoadMore={handleLoadMore}
                    />
                </SimpleTreeView>
            </div>
        </View>
    );
};
