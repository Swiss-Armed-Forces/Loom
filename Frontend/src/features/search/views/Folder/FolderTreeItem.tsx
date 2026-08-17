import {
    Article,
    ArrowDropDown,
    ArrowRight,
    FiberManualRecord,
    Flag,
    Folder,
    FolderOpen,
    FolderSpecial,
    MoreHoriz,
    Preview,
} from "@mui/icons-material";
import {
    Chip,
    IconButton,
    Skeleton,
    Stack,
    Tooltip,
    Typography,
} from "@mui/material";
import { TreeItem } from "@mui/x-tree-view";
import React, { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";

import { useAppSelector } from "@app/hooks";
import {
    openFileTabThunk,
    selectQuery,
    updateQuery,
} from "@app/slices/searchSlice";
import { AppDispatch } from "@app/store";
import { SearchQueryField } from "@features/common/utils/enums";
import { updateFieldOfQuery } from "@features/common/utils/helpers";

import { FolderTree, ROOT_NODE, PATH_SEPARATOR } from "./folderViewState";
import { hasUnloadedChildren } from "./util";

const FOLDER_CHIP_FIELDS = [
    SearchQueryField.ParentPath,
    SearchQueryField.FullPathTree,
    SearchQueryField.FullPathKeyword,
    SearchQueryField.Seen,
    SearchQueryField.Flagged,
];

interface NodeCountBadgesProps {
    flaggedCount?: number;
    unseenCount?: number;
    directChildrenCount?: number;
    fileCount?: number;
    onFlaggedClick: (e: React.MouseEvent) => void;
    onUnseenClick: (e: React.MouseEvent) => void;
    onDirectChildrenClick: (e: React.MouseEvent) => void;
    onFileCountClick: (e: React.MouseEvent) => void;
}

export const NodeCountBadges = ({
    flaggedCount,
    unseenCount,
    directChildrenCount,
    fileCount,
    onFlaggedClick,
    onUnseenClick,
    onDirectChildrenClick,
    onFileCountClick,
}: NodeCountBadgesProps) => {
    const { t } = useTranslation();
    return (
        <>
            {(flaggedCount ?? 0) > 0 && (
                <Tooltip title={t("folderView.flaggedCountTooltip")}>
                    <Chip
                        size="small"
                        color="error"
                        variant="outlined"
                        icon={<Flag />}
                        label={flaggedCount}
                        onClick={onFlaggedClick}
                    />
                </Tooltip>
            )}
            {(unseenCount ?? 0) > 0 && (
                <Tooltip title={t("folderView.unseenCountTooltip")}>
                    <Chip
                        size="small"
                        color="primary"
                        variant="outlined"
                        icon={<FiberManualRecord />}
                        label={unseenCount}
                        onClick={onUnseenClick}
                    />
                </Tooltip>
            )}
            {(directChildrenCount ?? 0) > 0 && (
                <Tooltip title={t("folderView.directChildrenCountTooltip")}>
                    <Chip
                        size="small"
                        icon={<FolderOpen />}
                        label={directChildrenCount}
                        onClick={onDirectChildrenClick}
                    />
                </Tooltip>
            )}
            {(fileCount ?? 0) > 0 && (
                <Tooltip title={t("folderView.fileCountTooltip")}>
                    <Chip
                        size="small"
                        icon={<Article />}
                        label={fileCount}
                        onClick={onFileCountClick}
                    />
                </Tooltip>
            )}
        </>
    );
};

export const NodeViewDetailsButton = ({ fileId }: { fileId: string }) => {
    const { t } = useTranslation();
    const dispatch = useDispatch<AppDispatch>();
    return (
        <Tooltip title={t("generalSearchView.viewDetails")}>
            <IconButton
                size="small"
                onClick={(e) => {
                    e.stopPropagation();
                    dispatch(
                        openFileTabThunk({ fileId, background: e.ctrlKey }),
                    );
                }}
            >
                <Preview fontSize="small" />
            </IconButton>
        </Tooltip>
    );
};

const getIconOfNode = (node: FolderTree): React.ElementType | undefined => {
    if (node.id === ROOT_NODE.id) return FolderSpecial;
    if (node.fileId) return Article;
    return Folder;
};

// Used to suppress the expand arrow while a node's children are being fetched.
// The arrow should only appear once we know children exist, not during loading.
const NullIcon = () => null;

export interface FolderViewNodeProps {
    tree: FolderTree;
    activeTabFileId?: string | null;
    onLoadMore: (nodeId: string) => void;
}

export const FolderViewNode = React.memo(
    function FolderViewNode({
        tree,
        activeTabFileId,
        onLoadMore,
    }: FolderViewNodeProps) {
        const { t } = useTranslation();
        const dispatch = useDispatch<AppDispatch>();
        const searchQuery = useAppSelector(selectQuery);

        if (!tree?.id) {
            return null;
        }

        const fileId = tree.fileId;
        const isActiveTab = fileId !== undefined && fileId === activeTabFileId;
        const isRoot = tree.id === ROOT_NODE.id;

        const NodeIcon = getIconOfNode(tree);

        // Show "Load more" when there are more backend pages to fetch.
        const hasMore = !!tree.nextPageCursor;

        const handleDirectChildrenClick = (e: React.MouseEvent) => {
            e.stopPropagation();
            dispatch(
                updateQuery({
                    query: updateFieldOfQuery(
                        searchQuery?.query ?? "",
                        SearchQueryField.ParentPath,
                        isRoot ? "*" : tree.id,
                        isRoot,
                        e.shiftKey,
                        e.ctrlKey,
                        FOLDER_CHIP_FIELDS.filter(
                            (f) => f !== SearchQueryField.ParentPath,
                        ),
                    ),
                }),
            );
        };

        // Build a subtree base query for non-root nodes.  When the node
        // itself is a file, exclude it via NOT full_path.keyword so that the
        // result set matches the chip counts (which don't count the node).
        const subtreeBaseQuery = (query: string): string => {
            let base = updateFieldOfQuery(
                query,
                SearchQueryField.FullPathTree,
                tree.id,
                false,
                false,
                false,
                [
                    SearchQueryField.ParentPath,
                    SearchQueryField.FullPathKeyword,
                    SearchQueryField.Seen,
                    SearchQueryField.Flagged,
                ],
            );
            if (fileId !== undefined) {
                base = updateFieldOfQuery(
                    base,
                    SearchQueryField.FullPathKeyword,
                    tree.id,
                    false,
                    true,
                    false,
                    [SearchQueryField.ParentPath],
                );
            }
            return base;
        };

        const handleFileCountClick = (e: React.MouseEvent) => {
            e.stopPropagation();
            if (isRoot) {
                dispatch(
                    updateQuery({
                        query: updateFieldOfQuery(
                            searchQuery?.query ?? "",
                            SearchQueryField.ParentPath,
                            "*",
                            true,
                            e.shiftKey,
                            e.ctrlKey,
                            FOLDER_CHIP_FIELDS.filter(
                                (f) => f !== SearchQueryField.ParentPath,
                            ),
                        ),
                    }),
                );
            } else {
                dispatch(
                    updateQuery({
                        query: subtreeBaseQuery(searchQuery?.query ?? ""),
                    }),
                );
            }
        };

        const handleFlaggedClick = (e: React.MouseEvent) => {
            e.stopPropagation();
            const base = isRoot
                ? (searchQuery?.query ?? "")
                : subtreeBaseQuery(searchQuery?.query ?? "");
            dispatch(
                updateQuery({
                    query: updateFieldOfQuery(
                        base,
                        SearchQueryField.Flagged,
                        "true",
                        false,
                        false,
                        false,
                        [SearchQueryField.Seen],
                    ),
                }),
            );
        };

        const handleUnseenClick = (e: React.MouseEvent) => {
            e.stopPropagation();
            const base = isRoot
                ? (searchQuery?.query ?? "")
                : subtreeBaseQuery(searchQuery?.query ?? "");
            dispatch(
                updateQuery({
                    query: updateFieldOfQuery(
                        base,
                        SearchQueryField.Seen,
                        "false",
                        false,
                        false,
                        false,
                        [SearchQueryField.Flagged],
                    ),
                }),
            );
        };

        const label = (
            <Stack
                key={tree.id + "-label"}
                direction="row"
                spacing={0.5}
                sx={{ alignItems: "center", width: "100%" }}
                {...(isRoot && {
                    "data-tour": "folder-tree-node",
                })}
            >
                {NodeIcon && (
                    <NodeIcon
                        sx={{ fontSize: "1rem", flexShrink: 0, opacity: 0.75 }}
                    />
                )}
                <Stack
                    direction="row"
                    spacing={0.5}
                    sx={{ alignItems: "center", flex: 1, minWidth: 0 }}
                >
                    <Typography
                        noWrap
                        variant="body2"
                        sx={{
                            ...(tree.isUnseen && { fontWeight: "bold" }),
                            ...(tree.isFlagged && { color: "error.main" }),
                        }}
                    >
                        {isRoot
                            ? tree.label
                            : tree.id.split(PATH_SEPARATOR).at(-1)}
                    </Typography>
                    <NodeCountBadges
                        flaggedCount={tree.flaggedCount}
                        unseenCount={tree.unseenCount}
                        directChildrenCount={tree.directChildrenCount}
                        fileCount={tree.fileCount}
                        onFlaggedClick={handleFlaggedClick}
                        onUnseenClick={handleUnseenClick}
                        onDirectChildrenClick={handleDirectChildrenClick}
                        onFileCountClick={handleFileCountClick}
                    />
                </Stack>
                {fileId !== undefined && (
                    <NodeViewDetailsButton fileId={fileId} />
                )}
            </Stack>
        );

        const children: ReactNode[] = Object.values(tree.children ?? {}).map(
            (c) => (
                <FolderViewNode
                    key={c.id}
                    tree={c}
                    activeTabFileId={activeTabFileId}
                    onLoadMore={onLoadMore}
                />
            ),
        );

        // Render a hidden placeholder for unloaded, non-empty nodes (directories
        // or files such as archives that have extracted children). MUI uses the
        // placeholder to decide whether to show the expand arrow.
        if (hasUnloadedChildren(tree)) {
            children.push(
                <TreeItem
                    key="placeholder"
                    itemId={tree.id + "-placeholder"}
                    label=""
                    sx={{ display: "none" }}
                />,
            );
        }

        if (hasMore) {
            children.push(
                <TreeItem
                    key="load-more"
                    itemId={"load-more-" + tree.id}
                    label={
                        <Stack
                            direction="row"
                            spacing={0.5}
                            sx={{
                                alignItems: "center",
                                color: "text.secondary",
                                py: 0.25,
                            }}
                        >
                            <MoreHoriz sx={{ fontSize: "0.9rem" }} />
                            <Typography
                                variant="caption"
                                sx={{
                                    fontStyle: "italic",
                                    letterSpacing: "0.02em",
                                }}
                            >
                                {t("folderView.loadMore")}
                            </Typography>
                        </Stack>
                    }
                    onClick={(e) => {
                        e.stopPropagation();
                        onLoadMore(tree.id);
                    }}
                    sx={{
                        "& > .MuiTreeItem-content": {
                            opacity: 0.7,
                            "&:hover": { opacity: 1 },
                        },
                    }}
                />,
            );
        }

        return (
            <TreeItem
                key={tree.id}
                itemId={tree.id}
                label={label}
                slots={
                    tree.loading
                        ? { expandIcon: NullIcon, collapseIcon: ArrowDropDown }
                        : {
                              expandIcon: ArrowRight,
                              collapseIcon: ArrowDropDown,
                          }
                }
                sx={
                    isActiveTab
                        ? {
                              "& > .MuiTreeItem-content": {
                                  borderLeft: "2px solid",
                                  borderColor: "primary.main",
                                  borderRadius: "0 4px 4px 0",
                                  bgcolor: "primary.main",
                                  color: "primary.contrastText",
                                  "&:hover": { bgcolor: "primary.dark" },
                              },
                          }
                        : undefined
                }
            >
                {!!tree.loading && (
                    <Skeleton key="loading-indicator" variant="text" />
                )}
                {children}
            </TreeItem>
        );
    },
    (prev, next) =>
        prev.tree === next.tree &&
        prev.activeTabFileId === next.activeTabFileId &&
        prev.onLoadMore === next.onLoadMore,
);
