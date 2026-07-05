import {
    FiberManualRecord,
    Flag,
    ManageSearch,
    Preview,
} from "@mui/icons-material";
import {
    Box,
    BoxProps,
    IconButton,
    List,
    ListItemButton,
    ListItemText,
    Skeleton,
    Stack,
    Tooltip,
    Typography,
    styled,
} from "@mui/material";
import { SimpleTreeView } from "@mui/x-tree-view";
import {
    Dispatch,
    useCallback,
    useEffect,
    useMemo,
    useReducer,
    useRef,
    useState,
} from "react";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";
import { toast } from "react-toastify";

import type { TreeNodeModel } from "@app/api/index";
import { getTreeLevelNodeLimit, searchTree } from "@app/api/index";
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
    openFileTabThunk,
    selectActiveTabFileId,
    selectFiles,
    selectHighlightedFileId,
    selectQuery,
    selectWebSocketPubSubMessage,
    setActiveTabFileId,
    setHighlightedIndex,
    setTemporaryFileId,
    updateQuery,
} from "@app/slices/searchSlice";
import { AppDispatch } from "@app/store";
import { SearchQueryField } from "@features/common/utils/enums";
import { updateFieldOfQuery } from "@features/common/utils/helpers";
import { SearchQuery } from "@features/common/utils/model";

import { FolderViewNode } from "./FolderTreeItem";
import styles from "./FolderView.module.css";
import { folderViewReducer } from "./folderViewReducer";
import {
    FolderTree,
    FolderViewAction,
    FolderViewActionType,
    ROOT_NODE,
    PATH_SEPARATOR,
} from "./folderViewState";
import { cloneTree, findAncestorNodeIds, findTreeNode } from "./util";

// Collect all fileIds present in the loaded tree nodes.
const collectTreeFileIds = (
    node: FolderTree,
    result: Set<string> = new Set(),
): Set<string> => {
    if (node.fileId) result.add(node.fileId);
    Object.values(node.children ?? {}).forEach((child) =>
        collectTreeFileIds(child, result),
    );
    return result;
};

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
    let children: TreeNodeModel[] | FolderTree[];
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
            children.map(async (child: TreeNodeModel | FolderTree) => {
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
    const [maxChildren, setMaxChildren] = useState(FALLBACK_MAX_CHILDREN_COUNT);
    const [folderState, folderDispatch] = useReducer(folderViewReducer, {
        tree: cloneTree(ROOT_NODE),
        expandedNodes: [],
    });
    const folderStateRef = useRef(folderState);
    folderStateRef.current = folderState;
    const searchQueryRef = useRef(searchQuery);
    searchQueryRef.current = searchQuery;
    // Tracks only nodes the user explicitly expanded/collapsed. Auto-expanded
    // ancestors (from card/tab navigation) are not stored here so they are
    // discarded when the focused file changes.
    const [userExpandedNodes, setUserExpandedNodes] = useState<string[]>([]);
    // Whether the initial auto-expand has been synced into userExpandedNodes.
    // After the first tree load, initial auto-expanded nodes are promoted into
    // the user snapshot so that WebSocket refreshes (which re-trigger the
    // auto-expand effect) never collapse them.
    const initialExpandSynced = useRef(false);
    // Tracks which fileIds the FolderView has subscribed to for WS updates so
    // that we can diff on tree changes and unsubscribe cleanly on reset.
    const subscribedTreeFileIds = useRef(new Set<string>());

    useEffect(() => {
        if (
            !initialExpandSynced.current &&
            folderState.expandedNodes.length > 0
        ) {
            setUserExpandedNodes([...folderState.expandedNodes]);
            initialExpandSynced.current = true;
        }
    }, [folderState.expandedNodes]);

    // Maintain WS subscriptions for all file nodes currently loaded in the
    // tree. This ensures fileUpdate messages arrive even when those files are
    // not visible as result cards and no detail tab is open for them.
    useEffect(() => {
        const currentFileIds = collectTreeFileIds(folderState.tree);
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
    }, [folderState.tree, dispatch]);

    // Unsubscribe all channels on unmount only
    useEffect(() => {
        const subscribedIds = subscribedTreeFileIds.current;
        return () => {
            subscribedIds.forEach((fileId) =>
                unsubscribeChannel(fileId, dispatch),
            );
            subscribedIds.clear();
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const handleExpandedItemsChange = (
        _: React.SyntheticEvent | null,
        nodeIds: string[],
    ) => {
        // Compute what the user toggled by diffing against the current display
        // state, then apply only that delta to the user snapshot.
        setUserExpandedNodes((prev) => {
            const added = nodeIds.find(
                (id) => !folderState.expandedNodes.includes(id),
            );
            const removed = folderState.expandedNodes.find(
                (id) => !nodeIds.includes(id),
            );
            if (added) return [...prev, added];
            if (removed) return prev.filter((id) => id !== removed);
            return prev;
        });
        folderDispatch({
            type: FolderViewActionType.EXPANDED_NODES_CHANGED,
            expandedNodes: nodeIds,
        });
    };

    // Pre-compute file ID array used in handleItemClick — includes stale files
    // to match the ordering used by selectHighlightedFileId.
    const allMetaFileIds = useMemo(
        () => Object.keys(files).filter((id) => files[id].meta !== null),
        [files],
    );

    const handleItemClick = (path: string) => {
        const node = findTreeNode(folderState.tree, path);
        if (!node) return;

        // If this node has a fileId, navigate to it in the results panel
        if (node.fileId) {
            // Use allMetaFileIds (includes stale) so the index matches
            // selectHighlightedFileId which also includes stale files.
            const index = allMetaFileIds.indexOf(node.fileId);
            if (index !== -1) {
                dispatch(setActiveTabFileId(null));
                dispatch(setHighlightedIndex(index));
            } else {
                // File not in current results — show as temporary card.
                const tempIndex = allMetaFileIds.length;
                dispatch(setTemporaryFileId(node.fileId));
                dispatch(setActiveTabFileId(null));
                dispatch(setHighlightedIndex(tempIndex));
                dispatch(fetchPreview({ fileId: node.fileId }));
            }
        }

        // Also load children (for folder nodes and container files like emails)
        if (searchQuery?.query) {
            loadChildren(node, searchQuery, path, folderDispatch).catch(
                (err) => {
                    toast.error(
                        "Cannot load tree search results. Error: " +
                            (err["detail"] ? err["detail"] : err),
                    );
                },
            );
        }
    };

    // Reload the already-loaded ancestor paths of the given file so that counts
    // (unseen, flagged) and node styling stay fresh. Returns a cleanup function
    // that cancels any in-flight dispatches (for use as a useEffect cleanup).
    // Reads tree and searchQuery via refs so the callback identity is stable
    // and does not trigger re-runs of effects that depend on it when the tree
    // changes after a CHILDREN_ADDED dispatch.
    const reloadAncestors = useCallback(
        (fileId: string) => {
            const searchQuery = searchQueryRef.current;
            if (!searchQuery) return undefined;
            const tree = folderStateRef.current.tree;
            // findAncestorNodeIds returns the path IDs of all ancestors of the
            // file node — these are exactly the directory paths whose counts are
            // affected by a state change on this file.
            const ancestors = findAncestorNodeIds(tree, fileId);
            if (!ancestors) return undefined;

            let cancelled = false;
            // Note: in-flight searchTree requests cannot be aborted because the
            // generated API client does not expose an AbortSignal parameter.
            // The cancelled flag prevents stale dispatches from completing.
            void Promise.all(
                ancestors
                    .filter((path) => findTreeNode(tree, path)?.children)
                    .map((path) =>
                        searchTree(searchQuery, path)
                            .then((children) => {
                                if (cancelled) return;
                                folderDispatch({
                                    type: FolderViewActionType.CHILDREN_ADDED,
                                    children,
                                    parentPath: path,
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
                            }),
                    ),
            );
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

    // When the focused file changes (highlighted index or active tab), reload
    // its ancestor paths so counts stay fresh for the newly focused file.
    // Debounced to avoid a burst of API requests during rapid arrow-key navigation.
    useEffect(() => {
        if (!focusedFileId) return;
        const id = setTimeout(() => {
            reloadAncestors(focusedFileId);
        }, 200);
        return () => clearTimeout(id);
    }, [focusedFileId, reloadAncestors]);

    useEffect(() => {
        if (!focusedFileId || !searchQuery) return;

        // If the node is already in the tree, expand all its ancestors.
        // Start from userExpandedNodes (the snapshot of manual expansions) so
        // that auto-expansions from a previous navigation are not carried over.
        const ancestors = findAncestorNodeIds(folderState.tree, focusedFileId);
        if (ancestors !== null) {
            const newExpanded = Array.from(
                new Set([...userExpandedNodes, ...ancestors]),
            );
            folderDispatch({
                type: FolderViewActionType.EXPANDED_NODES_CHANGED,
                expandedNodes: newExpanded,
            });
            return;
        }

        // Node not yet in tree — load each ancestor level that is missing.
        // focusedFilePath comes from preview which may load slightly after
        // focusedFileId changes; the effect re-runs once it arrives.
        if (!focusedFilePath) return;

        // Walk up from the file path to build ancestor node IDs.
        // Paths use a //source/name format so we must not strip the prefix —
        // use lastIndexOf instead of split/filter to preserve it.
        const ancestorPaths: string[] = [];
        let current = focusedFilePath;
        while (true) {
            const lastSlash = current.lastIndexOf(PATH_SEPARATOR);
            if (lastSlash < 0) break;
            current = current.slice(0, lastSlash);
            if (!current || current === ROOT_NODE.id) break;
            ancestorPaths.unshift(current);
        }
        ancestorPaths.unshift(ROOT_NODE.id);

        // Load the first ancestor level that is missing children. Each
        // CHILDREN_ADDED dispatch updates folderState.tree, re-triggering
        // this effect so we walk down one level at a time until the target
        // node exists and findAncestorNodeIds succeeds.
        const firstMissing = ancestorPaths.find((path) => {
            const node = findTreeNode(folderState.tree, path);
            return node !== undefined && !node.children && !node.loading;
        });
        if (firstMissing) {
            loadChildren(
                findTreeNode(folderState.tree, firstMissing) ?? null,
                searchQuery,
                firstMissing,
                folderDispatch,
                1,
            ).catch(() => {});
        }
    }, [
        focusedFileId,
        focusedFilePath,
        folderState.tree,
        searchQuery,
        userExpandedNodes,
    ]);

    useEffect(() => {
        getTreeLevelNodeLimit().then(setMaxChildren);
    }, []);

    useEffect(() => {
        folderDispatch({ type: FolderViewActionType.QUERY_CHANGED });
        setUserExpandedNodes([]);
        initialExpandSynced.current = false;
        subscribedTreeFileIds.current.forEach((fileId) =>
            unsubscribeChannel(fileId, dispatch),
        );
        subscribedTreeFileIds.current.clear();
    }, [searchQuery, folderDispatch, dispatch]);

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
        folderDispatch,
        dispatch,
    ]);

    const [filterResults, setFilterResults] = useState<TreeNodeModel[]>([]);
    const [filterLoading, setFilterLoading] = useState(false);
    const [filterTruncated, setFilterTruncated] = useState(false);

    useEffect(() => {
        if (!filter || !searchQuery) {
            setFilterResults([]);
            return;
        }
        const derivedQuery = `(${searchQuery.query}) filename:*${filter}*`;
        const timer = setTimeout(() => {
            setFilterLoading(true);
            searchTree(
                { ...searchQuery, query: derivedQuery },
                ROOT_NODE.id,
                true,
            )
                .then((results) => {
                    // The backend bucket size is maxChildren + 1; if the raw
                    // result count reaches that, the list was silently capped.
                    setFilterTruncated(results.length > maxChildren);
                    setFilterResults(
                        results.filter((n) => n.fileId !== undefined),
                    );
                })
                .catch(() => toast.error("Cannot load filter results."))
                .finally(() => setFilterLoading(false));
        }, 300);
        return () => clearTimeout(timer);
    }, [filter, searchQuery, maxChildren]);

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
                                    const index =
                                        allMetaFileIds.indexOf(fileId);
                                    if (index !== -1) {
                                        dispatch(setActiveTabFileId(null));
                                        dispatch(setHighlightedIndex(index));
                                    } else {
                                        dispatch(setTemporaryFileId(fileId));
                                        dispatch(setActiveTabFileId(null));
                                        dispatch(
                                            setHighlightedIndex(
                                                allMetaFileIds.length,
                                            ),
                                        );
                                        dispatch(fetchPreview({ fileId }));
                                    }
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
                                            {(node.unseenCount ?? 0) > 0 && (
                                                <Tooltip
                                                    title={t(
                                                        "folderView.unseenCountTooltip",
                                                    )}
                                                >
                                                    <Box
                                                        sx={{
                                                            display: "flex",
                                                            alignItems:
                                                                "center",
                                                            gap: 0.25,
                                                            flexShrink: 0,
                                                            color: "primary.main",
                                                        }}
                                                    >
                                                        <FiberManualRecord
                                                            sx={{
                                                                fontSize:
                                                                    "0.45rem",
                                                            }}
                                                        />
                                                        <Typography
                                                            variant="caption"
                                                            sx={{
                                                                lineHeight: 1,
                                                                color: "inherit",
                                                            }}
                                                        >
                                                            {node.unseenCount}
                                                        </Typography>
                                                    </Box>
                                                </Tooltip>
                                            )}
                                            {(node.flaggedCount ?? 0) > 0 && (
                                                <Tooltip
                                                    title={t(
                                                        "folderView.flaggedCountTooltip",
                                                    )}
                                                >
                                                    <Box
                                                        sx={{
                                                            display: "flex",
                                                            alignItems:
                                                                "center",
                                                            gap: 0.25,
                                                            flexShrink: 0,
                                                            color: "error.main",
                                                        }}
                                                    >
                                                        <Flag
                                                            sx={{
                                                                fontSize:
                                                                    "0.75rem",
                                                            }}
                                                        />
                                                        <Typography
                                                            variant="caption"
                                                            sx={{
                                                                lineHeight: 1,
                                                                color: "inherit",
                                                            }}
                                                        >
                                                            {node.flaggedCount}
                                                        </Typography>
                                                    </Box>
                                                </Tooltip>
                                            )}
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
                                <Tooltip
                                    title={t("generalSearchView.viewDetails")}
                                >
                                    <IconButton
                                        size="small"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            dispatch(
                                                openFileTabThunk({
                                                    fileId: fileId!,
                                                    background: e.ctrlKey,
                                                }),
                                            );
                                        }}
                                    >
                                        <Preview fontSize="small" />
                                    </IconButton>
                                </Tooltip>
                                <Tooltip
                                    title={t(
                                        "folderView.addPathToQueryTooltip",
                                    )}
                                >
                                    <IconButton
                                        size="small"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            dispatch(
                                                updateQuery({
                                                    query: updateFieldOfQuery(
                                                        searchQuery?.query ??
                                                            "",
                                                        SearchQueryField.Filename,
                                                        node.fullPath,
                                                        false,
                                                    ),
                                                }),
                                            );
                                        }}
                                    >
                                        <ManageSearch fontSize="small" />
                                    </IconButton>
                                </Tooltip>
                            </ListItemButton>
                        );
                    })}
                </List>
                {filterTruncated && (
                    <Typography
                        variant="caption"
                        sx={{ display: "block", px: 1, py: 0.5, opacity: 0.6 }}
                    >
                        {t("folderView.filterResultsLimitNote", {
                            limit: maxChildren,
                        })}
                    </Typography>
                )}
            </>
        );
    }

    return (
        <View>
            <div className={styles.treeView}>
                <SimpleTreeView
                    expandedItems={folderState.expandedNodes}
                    onExpandedItemsChange={handleExpandedItemsChange}
                    onItemClick={(_, itemId) => handleItemClick(itemId)}
                >
                    <FolderViewNode
                        tree={folderState.tree}
                        maxChildren={maxChildren}
                        activeTabFileId={focusedFileId}
                    />
                </SimpleTreeView>
            </div>
        </View>
    );
};
