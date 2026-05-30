import { ExpandMore, Label } from "@mui/icons-material";
import { Chip, Menu, MenuItem } from "@mui/material";
import { t } from "i18next";
import { FC, useMemo, useState } from "react";
import { toast } from "react-toastify";

import {
    deleteTagFromFile,
    GenericStatisticsModel,
    GetFilePreviewResponse,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks.ts";
import {
    openDialog,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import {
    selectQuery,
    setFilePreview,
    updateQuery,
} from "@app/slices/searchSlice";
import { DialogType, SearchQueryField } from "@features/common/utils/enums";
import {
    getColorFromString,
    getFontColorFromBackGroundColor,
    updateFieldOfQuery,
} from "@features/common/utils/helpers";

import styles from "./TagsList.module.css";

interface TagsListProps {
    tags: string[];
    filePreview?: GetFilePreviewResponse;
    tagStats?: GenericStatisticsModel;
    iconOnly?: boolean;
    maxVisible?: number;
}

export const TagsList = ({
    tags,
    filePreview,
    tagStats,
    iconOnly = false,
    maxVisible,
}: TagsListProps) => {
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const fileId = filePreview?.fileId;
    const [overflowAnchor, setOverflowAnchor] = useState<null | HTMLElement>(
        null,
    );

    const sortedTags = useMemo(
        () => tags.slice().sort((a, b) => a.localeCompare(b)),
        [tags],
    );

    const searchForTag = (tagName: string) => {
        dispatch(
            updateQuery({
                query: updateFieldOfQuery(
                    searchQuery?.query ?? "",
                    SearchQueryField.Tags,
                    tagName,
                ),
            }),
        );
    };

    const getTagHitRate = (tagName: string): number => {
        const tagData = tagStats?.data ?? [];
        const total = tagStats?.fileCount ?? 1;
        const tag = tagData.find((t) => t.name === tagName);
        return tag ? (tag.hitsCount / total) * 100 : 0;
    };

    const handleDeleteTagFromFile = async (tag: string) => {
        if (!fileId) return;

        try {
            dispatch(startLoadingIndicator());
            await deleteTagFromFile(fileId, tag);
            dispatch(
                setFilePreview({
                    ...filePreview,
                    tags: filePreview.tags
                        ? filePreview.tags.filter((t) => t !== tag)
                        : [],
                }),
            );
            toast.success(t("tagsList.scheduledRemoveTagFromFileToast"));
        } catch (err) {
            toast.error(t("tagsList.scheduledRemoveErrorToast", { err }));
        } finally {
            dispatch(stopLoadingIndicator());
        }
    };

    const handleDeleteClick = (tag: string) => {
        if (fileId) {
            handleDeleteTagFromFile(tag);
        } else {
            dispatch(
                openDialog({
                    id: "",
                    type: DialogType.DeleteTagGlobally,
                    props: { tag },
                }),
            );
        }
    };

    const getTagLabel = (tag: string): string => {
        if (!tagStats) return tag;
        const hitRate = getTagHitRate(tag);
        return `${tag} (${hitRate.toFixed(1)}%)`;
    };

    const visibleTags =
        maxVisible !== undefined ? sortedTags.slice(0, maxVisible) : sortedTags;
    const overflowTags =
        maxVisible !== undefined ? sortedTags.slice(maxVisible) : [];

    return (
        <div
            className={
                iconOnly
                    ? `${styles.tagsList} ${styles.closed}`
                    : styles.tagsList
            }
        >
            {visibleTags.map((tag) => (
                <TagChip
                    key={fileId + tag}
                    tag={tag}
                    iconOnly={iconOnly}
                    label={getTagLabel(tag)}
                    onSearch={searchForTag}
                    onDelete={
                        iconOnly ? undefined : () => handleDeleteClick(tag)
                    }
                />
            ))}
            {overflowTags.length > 0 && (
                <>
                    <Chip
                        className={styles.tagChip}
                        size="small"
                        icon={<Label />}
                        label={`+${overflowTags.length}`}
                        onClick={(e) => setOverflowAnchor(e.currentTarget)}
                        onDelete={(e) => setOverflowAnchor(e.currentTarget)}
                        deleteIcon={<ExpandMore />}
                        title={t("tagsList.moreTagsTooltip", {
                            count: overflowTags.length,
                        })}
                    />
                    <Menu
                        anchorEl={overflowAnchor}
                        open={Boolean(overflowAnchor)}
                        onClose={() => setOverflowAnchor(null)}
                        anchorOrigin={{
                            vertical: "bottom",
                            horizontal: "left",
                        }}
                        transformOrigin={{
                            vertical: "top",
                            horizontal: "left",
                        }}
                    >
                        {overflowTags.map((tag) => (
                            <MenuItem
                                key={fileId + tag + "-overflow"}
                                sx={{ gap: 1 }}
                                disableRipple
                            >
                                <TagChip
                                    tag={tag}
                                    iconOnly={false}
                                    label={getTagLabel(tag)}
                                    onSearch={(t) => {
                                        setOverflowAnchor(null);
                                        searchForTag(t);
                                    }}
                                    onDelete={
                                        iconOnly
                                            ? undefined
                                            : () => handleDeleteClick(tag)
                                    }
                                />
                            </MenuItem>
                        ))}
                    </Menu>
                </>
            )}
        </div>
    );
};

interface TagChipProps {
    tag: string;
    iconOnly: boolean;
    label: string;
    onSearch: (tag: string) => void;
    onDelete?: () => void;
}

const TagChip: FC<TagChipProps> = ({
    tag,
    iconOnly,
    label,
    onSearch,
    onDelete,
}) => {
    const backgroundColor = getColorFromString(tag);
    const color = getFontColorFromBackGroundColor(backgroundColor);

    return (
        <Chip
            className={styles.tagChip}
            size={iconOnly ? undefined : "small"}
            sx={{ backgroundColor, color }}
            label={iconOnly ? undefined : label}
            title={iconOnly ? tag : undefined}
            onClick={() => {
                onSearch(tag);
            }}
            onDelete={onDelete}
        />
    );
};
