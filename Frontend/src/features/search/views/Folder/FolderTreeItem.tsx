import {
    Article,
    FiberManualRecord,
    Flag,
    Folder,
    FolderSpecial,
    ManageSearch,
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

const MoreItemsHiddenLabel = ({ parentPath }: { parentPath: string }) => {
    const { t } = useTranslation();
    return (
        <TreeItem
            itemId={"more-elements-" + parentPath}
            label={t("folderView.moreElementsHidden")}
            title={t("folderView.moreElementsHiddenTooltip")}
            disabled
        />
    );
};

const getIconOfNode = (node: FolderTree): React.ElementType | undefined => {
    if (node.id == ROOT_NODE.id) {
        return FolderSpecial;
    } else if (Object.keys(node.children ?? {}).length) {
        return Folder;
    } else {
        return Article;
    }
};

export interface FolderViewNodeProps {
    tree: FolderTree;
    maxChildren: number;
    activeTabFileId?: string | null;
}

export const FolderViewNode = React.memo(function FolderViewNode({
    tree,
    maxChildren,
    activeTabFileId,
}: FolderViewNodeProps) {
    const { t } = useTranslation();
    const searchQuery = useAppSelector(selectQuery);
    const dispatch = useDispatch<AppDispatch>();

    if (!tree?.id) {
        return null;
    }

    const totalChildren = Object.keys(tree.children ?? {}).length;
    const fileId = tree.fileId;
    const isActiveTab = fileId !== undefined && fileId === activeTabFileId;

    const label = (
        <Stack
            key={tree.id + "-label"}
            direction="row"
            spacing={0.5}
            sx={{ alignItems: "center", width: "100%" }}
        >
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
                {(tree.unseenCount ?? 0) > 0 && (
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
                                {tree.unseenCount}
                            </Typography>
                        </Box>
                    </Tooltip>
                )}
                {(tree.flaggedCount ?? 0) > 0 && (
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
                                {tree.flaggedCount}
                            </Typography>
                        </Box>
                    </Tooltip>
                )}
            </Stack>
            {fileId !== undefined && (
                <Tooltip title={t("generalSearchView.viewDetails")}>
                    <IconButton
                        size="small"
                        onClick={(e) => {
                            e.stopPropagation();
                            dispatch(
                                openFileTabThunk({
                                    fileId,
                                    background: e.ctrlKey,
                                }),
                            );
                        }}
                    >
                        <Preview fontSize="small" />
                    </IconButton>
                </Tooltip>
            )}
            <Tooltip title={t("folderView.addPathToQueryTooltip")}>
                <IconButton
                    size="small"
                    onClick={(e) => {
                        e.stopPropagation();
                        const isRoot = tree.id === ROOT_NODE.id;
                        dispatch(
                            updateQuery({
                                query: updateFieldOfQuery(
                                    searchQuery?.query ?? "",
                                    SearchQueryField.Filename,
                                    isRoot ? "*" : tree.id,
                                    isRoot,
                                ),
                            }),
                        );
                    }}
                >
                    <ManageSearch fontSize="small" />
                </IconButton>
            </Tooltip>
        </Stack>
    );

    const children: ReactNode[] =
        (!!tree.children &&
            Object.values(tree.children)
                .slice(0, maxChildren - 1)
                .map((c) => (
                    <FolderViewNode
                        key={c.id}
                        tree={c}
                        maxChildren={maxChildren}
                        activeTabFileId={activeTabFileId}
                    />
                ))) ||
        [];

    if (totalChildren >= maxChildren) {
        children.push(
            <MoreItemsHiddenLabel key="more-elements" parentPath={tree.id} />,
        );
    }

    return (
        <TreeItem
            key={tree.id}
            itemId={tree.id}
            label={label}
            slots={{ icon: getIconOfNode(tree) }}
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
});
