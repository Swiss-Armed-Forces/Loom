import {
    Article,
    ArrowDropDown,
    ArrowRight,
    FiberManualRecord,
    Flag,
    Folder,
    FolderSpecial,
    ManageSearch,
    MoreHoriz,
    Preview,
} from "@mui/icons-material";
import {
    Box,
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

interface NodeCountBadgesProps {
    flaggedCount?: number;
    unseenCount?: number;
    fileCount?: number;
}

export const NodeCountBadges = ({
    flaggedCount,
    unseenCount,
    fileCount,
}: NodeCountBadgesProps) => {
    const { t } = useTranslation();
    return (
        <>
            {(flaggedCount ?? 0) > 0 && (
                <Tooltip title={t("folderView.flaggedCountTooltip")}>
                    <Box
                        sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 0.25,
                            flexShrink: 0,
                            color: "error.main",
                        }}
                    >
                        <Flag sx={{ fontSize: "0.75rem" }} />
                        <Typography
                            variant="caption"
                            sx={{ lineHeight: 1, color: "inherit" }}
                        >
                            {flaggedCount}
                        </Typography>
                    </Box>
                </Tooltip>
            )}
            {(unseenCount ?? 0) > 0 && (
                <Tooltip title={t("folderView.unseenCountTooltip")}>
                    <Box
                        sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 0.25,
                            flexShrink: 0,
                            color: "primary.main",
                        }}
                    >
                        <FiberManualRecord sx={{ fontSize: "0.45rem" }} />
                        <Typography
                            variant="caption"
                            sx={{ lineHeight: 1, color: "inherit" }}
                        >
                            {unseenCount}
                        </Typography>
                    </Box>
                </Tooltip>
            )}
            {(fileCount ?? 0) > 0 && (
                <Tooltip title={t("folderView.fileCountTooltip")}>
                    <Box
                        sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 0.25,
                            flexShrink: 0,
                            color: "text.secondary",
                        }}
                    >
                        <Article sx={{ fontSize: "0.75rem" }} />
                        <Typography
                            variant="caption"
                            sx={{ lineHeight: 1, color: "inherit" }}
                        >
                            {fileCount}
                        </Typography>
                    </Box>
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

export const NodeAddToQueryButton = ({
    path,
    isRoot = false,
}: {
    path: string;
    isRoot?: boolean;
}) => {
    const { t } = useTranslation();
    const dispatch = useDispatch<AppDispatch>();
    const searchQuery = useAppSelector(selectQuery);
    return (
        <Tooltip title={t("folderView.addPathToQueryTooltip")}>
            <IconButton
                size="small"
                onClick={(e) => {
                    e.stopPropagation();
                    dispatch(
                        updateQuery({
                            query: updateFieldOfQuery(
                                searchQuery?.query ?? "",
                                SearchQueryField.Filename,
                                isRoot ? "*" : path,
                                isRoot,
                                e.shiftKey,
                            ),
                        }),
                    );
                }}
            >
                <ManageSearch fontSize="small" />
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
    maxChildren: number;
    activeTabFileId?: string | null;
    onLoadMore: (nodeId: string) => void;
}

export const FolderViewNode = React.memo(
    function FolderViewNode({
        tree,
        maxChildren,
        activeTabFileId,
        onLoadMore,
    }: FolderViewNodeProps) {
        const { t } = useTranslation();

        if (!tree?.id) {
            return null;
        }

        const fileId = tree.fileId;
        const isActiveTab = fileId !== undefined && fileId === activeTabFileId;

        const NodeIcon = getIconOfNode(tree);

        // Show "Load more" when there are more backend pages to fetch.
        const hasMore = !!tree.nextPageCursor;

        const label = (
            <Stack
                key={tree.id + "-label"}
                direction="row"
                spacing={0.5}
                sx={{ alignItems: "center", width: "100%" }}
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
                        {tree.id === ROOT_NODE.id
                            ? tree.label
                            : tree.id.split(PATH_SEPARATOR).at(-1)}
                    </Typography>
                    <NodeCountBadges
                        flaggedCount={tree.flaggedCount}
                        unseenCount={tree.unseenCount}
                        fileCount={tree.fileCount}
                    />
                </Stack>
                {fileId !== undefined && (
                    <NodeViewDetailsButton fileId={fileId} />
                )}
                <NodeAddToQueryButton
                    path={tree.id}
                    isRoot={tree.id === ROOT_NODE.id}
                />
            </Stack>
        );

        const children: ReactNode[] = Object.values(tree.children ?? {}).map(
            (c) => (
                <FolderViewNode
                    key={c.id}
                    tree={c}
                    maxChildren={maxChildren}
                    activeTabFileId={activeTabFileId}
                    onLoadMore={onLoadMore}
                />
            ),
        );

        // Render a hidden placeholder child when we know the node has children
        // (fileCount > 0) but they haven't been fetched yet. Without this,
        // MUI won't show the expand arrow even though the node is expandable.
        // display:none keeps it invisible while still counting as a React child.
        if (
            tree.children === undefined &&
            !tree.loading &&
            (tree.fileCount ?? 0) > 0
        ) {
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
        prev.maxChildren === next.maxChildren &&
        prev.activeTabFileId === next.activeTabFileId &&
        prev.onLoadMore === next.onLoadMore,
);
