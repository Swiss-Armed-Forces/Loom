import { Article, Folder, FolderSpecial, Search } from "@mui/icons-material";
import {
    Box,
    BoxProps,
    Chip,
    IconButton,
    Skeleton,
    styled,
} from "@mui/material";
import { TreeItem } from "@mui/x-tree-view";
import { useDispatch } from "react-redux";
import { useAppSelector } from "../../../../app/hooks";
import { AppDispatch } from "../../../../app/store";
import { updateFilenameOfQuery } from "../../SearchQueryUtils";
import { selectQuery, updateQuery } from "../../searchSlice";
import { FolderTree, ROOT_NODE, PATH_SEPARATOR } from "./folderViewState";
import { ReactNode } from "react";
import { useTranslation } from "react-i18next";

const NodeLabel = styled(Box)<BoxProps>(() => ({
    display: "flex",
    gap: "0.5rem",
    alignItems: "center",
    "& .MuiChip-root": {
        alignItems: "end",
    },
}));

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

function getIconOfNode(node: FolderTree): React.ElementType | undefined {
    if (node.id == ROOT_NODE.id) {
        return FolderSpecial;
    } else if (Object.keys(node.children ?? {}).length) {
        return Folder;
    } else {
        return Article;
    }
}
export interface FolderViewNodeProps {
    tree: FolderTree;
    onClick: (path: string) => void;
    maxChildren: number;
}

export function FolderViewNode({
    tree,
    onClick,
    maxChildren,
}: FolderViewNodeProps) {
    const { t } = useTranslation();
    const searchQuery = useAppSelector(selectQuery);
    const dispatch = useDispatch<AppDispatch>();

    const handleUpdateQueryFilename = (newFilename: string) => {
        dispatch(
            updateQuery({
                query: updateFilenameOfQuery(
                    searchQuery?.query ?? "",
                    newFilename,
                ),
            }),
        );
    };

    if (!tree?.id) {
        return null;
    }

    const totalChildren = Object.keys(tree.children ?? {}).length;
    const label = (
        <NodeLabel key={tree.id + "-label"}>
            <span>
                {tree.id === ROOT_NODE.id
                    ? tree.label
                    : tree.id.split(PATH_SEPARATOR).at(-1)}
            </span>
            {(tree.fileCount ?? 0) > 0 && totalChildren > 0 && (
                <Chip label={tree.fileCount} size="small" />
            )}
            <IconButton
                onClick={() => handleUpdateQueryFilename(tree.id)}
                title={t("folderView.addPathToQueryTooltip")}
            >
                <Search />
            </IconButton>
        </NodeLabel>
    );

    const children: ReactNode[] =
        (!!tree.children &&
            Object.values(tree.children)
                .slice(0, maxChildren - 1)
                .map((c) => (
                    <FolderViewNode
                        key={c.id}
                        tree={c}
                        onClick={onClick}
                        maxChildren={maxChildren}
                    />
                ))) ||
        [];

    if (totalChildren > maxChildren) {
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
            onClick={() => onClick(tree.id)}
        >
            {!!tree.loading && (
                <Skeleton key="loading-indicator" variant="text" />
            )}
            {children}
        </TreeItem>
    );
}
