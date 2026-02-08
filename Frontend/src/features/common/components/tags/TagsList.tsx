import { Chip } from "@mui/material";
import { updateTagOfQuery } from "../../../search/SearchQueryUtils.ts";
import { selectQuery, updateQuery } from "../../../search/searchSlice.ts";
import {
    deleteTagFromFile,
    deleteTagFromFiles,
    GenericStatisticsModel,
} from "../../../../app/api";
import { FC, useState, useMemo } from "react";
import { useAppDispatch, useAppSelector } from "../../../../app/hooks.ts";
import styles from "./TagsList.module.css";
import { toast } from "react-toastify";
import { t } from "i18next";
import { ConfirmDialog } from "../../../search/components/ConfirmDialog.tsx";
import LabelIcon from "@mui/icons-material/Label";
import {
    startLoadingIndicator,
    stopLoadingIndicator,
} from "../../commonSlice.ts";
import {
    getColorFromString,
    getFontColorFromBackGroundColor,
} from "../../getColorFromString.ts";

interface TagsListProps {
    tags: string[];
    fileId?: string;
    tagStats?: GenericStatisticsModel;
    icon_only?: boolean;
}

export const TagsList: FC<TagsListProps> = ({
    tags,
    fileId,
    tagStats,
    icon_only = false,
}) => {
    const [tagInDeletion, setTagInDeletion] = useState<string | null>(null);
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);

    const sortedTags = useMemo(
        () => tags.slice().sort((a, b) => a.localeCompare(b)),
        [tags],
    );

    const searchForTag = (tagName: string) => {
        dispatch(
            updateQuery({
                query: updateTagOfQuery(searchQuery?.query ?? "", tagName),
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
            toast.success(t("tagsList.scheduledRemoveTagFromFileToast"));
        } catch (err) {
            toast.error(t("tagsList.scheduledRemoveErrorToast", { err }));
        } finally {
            dispatch(stopLoadingIndicator());
        }
    };

    const handleDeleteTagGlobally = async () => {
        if (!tagInDeletion) return;

        try {
            dispatch(startLoadingIndicator());
            await deleteTagFromFiles(tagInDeletion);
            setShowConfirmDialog(false);
            toast.success(t("tagsList.scheduledRemoveTagToast"));
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
            setTagInDeletion(tag);
            setShowConfirmDialog(true);
        }
    };

    const getTagLabel = (tag: string): string => {
        if (!tagStats) return tag;
        const hitRate = getTagHitRate(tag);
        return `${tag} (${hitRate.toFixed(1)}%)`;
    };

    return (
        <>
            <div
                className={
                    icon_only
                        ? `${styles.tagsList} ${styles.closed}`
                        : styles.tagsList
                }
            >
                {sortedTags.map((tag) => (
                    <TagChip
                        key={fileId + tag}
                        tag={tag}
                        iconOnly={icon_only}
                        label={getTagLabel(tag)}
                        onSearch={searchForTag}
                        onDelete={
                            icon_only ? undefined : () => handleDeleteClick(tag)
                        }
                    />
                ))}
            </div>

            {tagInDeletion && (
                <ConfirmDialog
                    open={showConfirmDialog}
                    text={t("confirmDialog.confirmTagDeletionText", {
                        tag: tagInDeletion,
                    })}
                    buttonText={t("confirmDialog.confirmTagDeletion")}
                    handleConfirmation={handleDeleteTagGlobally}
                    cancel={() => setShowConfirmDialog(false)}
                    icon={<LabelIcon />}
                />
            )}
        </>
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
            onClick={() => onSearch(tag)}
            onDelete={onDelete}
        />
    );
};
