import { Chip } from "@mui/material";
import stc from "string-to-color";
import { updateTagOfQuery } from "../../../search/SearchQueryUtils.ts";
import { selectQuery, setQuery } from "../../../search/searchSlice.ts";
import {
    deleteTagFromFile,
    deleteTagFromFiles,
    GenericStatisticsModel,
} from "../../../../app/api";
import { FC, useState } from "react";
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
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const [openConfirmDeleteTagGlobal, setOpenConfirmDeleteTagGlobal] =
        useState<boolean>(false);
    const searchForTag = (tagName: string) => {
        dispatch(
            setQuery({
                query: updateTagOfQuery(searchQuery?.query ?? "", tagName),
            }),
        );
    };

    const tagStatHitRate = (tagName: string) => {
        const tagData = tagStats?.data ?? [];
        const total = tagStats?.fileCount ?? 1; // happy typescript / eslint
        for (const tag of tagData) {
            if (tag.name === tagName) {
                return (tag.hitsCount / total) * 100;
            }
        }
        return 0;
    };

    const handleDeleteTagConfirmation = (tag: string) => {
        setTagInDeletion(tag);
        setOpenConfirmDeleteTagGlobal(true);
    };

    const handleDeleteTagFromFile = async (tag: string) => {
        if (!fileId) return;
        try {
            dispatch(startLoadingIndicator());
            await deleteTagFromFile(fileId, tag);
            toast.success(t("tagsList.scheduledRemoveTagFromFileToast"));
        } catch (err) {
            toast.error(
                t("tagsList.scheduledRemoveErrorToast", {
                    err: err,
                }),
            );
        } finally {
            dispatch(stopLoadingIndicator());
        }
    };

    const handleDeleteTag = async () => {
        if (!tagInDeletion) return;
        try {
            dispatch(startLoadingIndicator());
            await deleteTagFromFiles(tagInDeletion);
            setOpenConfirmDeleteTagGlobal(false);
            toast.success(t("tagsList.scheduledRemoveTagToast"));
        } catch (err) {
            toast.error(
                t("tagsList.scheduledRemoveErrorToast", {
                    err: err,
                }),
            );
        } finally {
            dispatch(stopLoadingIndicator());
        }
    };

    const calculateLuminance = (color: string) => {
        // convert hex to RGB
        const hex = color.substring(1);
        const r = parseInt(hex.substring(0, 2), 16) / 255;
        const g = parseInt(hex.substring(2, 4), 16) / 255;
        const b = parseInt(hex.substring(4, 6), 16) / 255;

        // calculate luminance
        const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        return luminance;
    };

    const fontColor = (color: string) => {
        const luminance = calculateLuminance(color);
        // get text color based on luminance
        return luminance > 0.5 ? "#000000" : "#ffffff";
    };

    return (
        <>
            {icon_only ? (
                <div className={`${styles.tagsList} ${styles.closed}`}>
                    {tags
                        .slice()
                        .sort((a, b) => a.localeCompare(b))
                        .map((tag) => (
                            <Chip
                                id={styles.sidebarChip}
                                style={{
                                    backgroundColor: stc(tag),
                                    color: fontColor(stc(tag)),
                                }}
                                key={fileId + tag}
                                onClick={() => searchForTag(tag)}
                                title={tag}
                            ></Chip>
                        ))}
                    {tagInDeletion && (
                        <ConfirmDialog
                            open={openConfirmDeleteTagGlobal}
                            text={t("confirmDialog.confirmTagDeletionText", {
                                tag: tagInDeletion,
                            })}
                            buttonText={t("confirmDialog.confirmTagDeletion")}
                            handleConfirmation={handleDeleteTag}
                            cancel={() => setOpenConfirmDeleteTagGlobal(false)}
                            icon={<LabelIcon />}
                        ></ConfirmDialog>
                    )}
                </div>
            ) : (
                <div className={styles.tagsList}>
                    {tags
                        .slice()
                        .sort((a, b) => a.localeCompare(b))
                        .map((tag) => (
                            <Chip
                                id={styles.sidebarChip}
                                size="small"
                                style={{
                                    backgroundColor: stc(tag),
                                    color: fontColor(stc(tag)),
                                }}
                                key={fileId + tag}
                                label={
                                    tagStats
                                        ? `${tag} (${tagStatHitRate(tag).toFixed(1)}%)`
                                        : tag
                                }
                                onDelete={
                                    fileId
                                        ? () => handleDeleteTagFromFile(tag)
                                        : () => handleDeleteTagConfirmation(tag)
                                }
                                onClick={() => searchForTag(tag)}
                            />
                        ))}
                    {tagInDeletion && (
                        <ConfirmDialog
                            open={openConfirmDeleteTagGlobal}
                            text={t("confirmDialog.confirmTagDeletionText", {
                                tag: tagInDeletion,
                            })}
                            buttonText={t("confirmDialog.confirmTagDeletion")}
                            handleConfirmation={handleDeleteTag}
                            cancel={() => setOpenConfirmDeleteTagGlobal(false)}
                            icon={<LabelIcon />}
                        ></ConfirmDialog>
                    )}
                </div>
            )}
        </>
    );
};
