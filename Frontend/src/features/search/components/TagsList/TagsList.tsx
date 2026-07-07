import { ExpandMore, Label } from "@mui/icons-material";
import { Chip, Menu, MenuItem, Tooltip } from "@mui/material";
import { t } from "i18next";
import { FC, useMemo, useState } from "react";
import { toast } from "react-toastify";

import { deleteTagFromFile, GetFilePreviewResponse } from "@app/api";
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
    iconOnly?: boolean;
    maxVisible?: number;
}

export const TagsList = ({
    tags,
    filePreview,
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

    const searchForTag = (tagName: string, negate = false) => {
        dispatch(
            updateQuery({
                query: updateFieldOfQuery(
                    searchQuery?.query ?? "",
                    SearchQueryField.Tags,
                    tagName,
                    false,
                    negate,
                ),
            }),
        );
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

    const getTagLabel = (tag: string): string => tag;

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
                                    onSearch={(t, negate) => {
                                        setOverflowAnchor(null);
                                        searchForTag(t, negate);
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
    onSearch: (tag: string, negate: boolean) => void;
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

    const chip = (
        <Chip
            className={styles.tagChip}
            size="small"
            sx={{ backgroundColor, color }}
            label={
                iconOnly
                    ? tag.length > 5
                        ? tag.slice(0, 5) + "…"
                        : tag
                    : label
            }
            onClick={(e) => {
                onSearch(tag, e.shiftKey);
            }}
            onDelete={onDelete}
        />
    );

    if (iconOnly) {
        return (
            <Tooltip title={tag} placement="right" enterDelay={200}>
                {chip}
            </Tooltip>
        );
    }

    return chip;
};
