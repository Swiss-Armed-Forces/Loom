import { Close, LabelOutlined } from "@mui/icons-material";
import { Autocomplete, Button, TextField } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
    GetFilePreviewResponse,
    ResponseError,
    addTagsToFile,
    addTagsToFiles,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    DialogProps,
    setBackgroundTaskSpinnerActive,
} from "@app/slices/commonSlice";
import {
    selectQuery,
    selectTags,
    setFilePreview,
} from "@app/slices/searchSlice";

import { DialogBase } from "../DialogBase";

interface AddTagsDialogProps extends DialogProps {
    filePreview?: GetFilePreviewResponse;
}

export const AddTagsDialog = ({
    id,
    onClose,
    filePreview,
}: AddTagsDialogProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();

    const searchQuery = useAppSelector(selectQuery);
    const existingTags = useAppSelector(selectTags);
    const [selectedTagsToAdd, setSelectedTagsToAdd] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const getErrorMessage = async (error: unknown): Promise<string> => {
        if (error instanceof ResponseError) {
            try {
                const errorData = await error.response.json();
                return errorData?.detail ?? JSON.stringify(errorData);
            } catch {
                return error.message || "Unknown error";
            }
        }

        if (error instanceof Error) {
            return error.message;
        }

        return String(error);
    };

    const startPersisting = async () => {
        if (!searchQuery) return;
        dispatch(setBackgroundTaskSpinnerActive());
        setIsLoading(true);
        try {
            if (filePreview && filePreview.fileId) {
                await addTagsToFile(filePreview?.fileId, selectedTagsToAdd);

                // Save tags locally
                dispatch(
                    setFilePreview({
                        ...filePreview,
                        tags: [
                            ...new Set([
                                ...(filePreview?.tags ?? []),
                                ...selectedTagsToAdd,
                            ]),
                        ],
                    }),
                );
            } else {
                await addTagsToFiles(searchQuery, selectedTagsToAdd);
            }
            toast.success(t("tags.scheduledToast"));
            onClose();
        } catch (error: any) {
            toast.error(
                t("tags.scheduledErrorToast", {
                    err: await getErrorMessage(error),
                }),
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <DialogBase
            id={id}
            onClose={onClose}
            title={t("tags.tagDialogTitle")}
            loading={isLoading}
            actions={
                <>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        tabIndex={2}
                        onClick={onClose}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        onClick={startPersisting}
                        disabled={selectedTagsToAdd.length === 0 || isLoading}
                        color="primary"
                        variant="contained"
                        startIcon={<LabelOutlined />}
                        tabIndex={1}
                    >
                        {t("tags.tagDialogSubmit")}
                    </Button>
                </>
            }
        >
            <p>{t("tags.tagDialogHint")}</p>
            <Autocomplete
                autoSelect
                freeSolo
                multiple
                options={existingTags}
                onChange={(_e, value) => setSelectedTagsToAdd(value)}
                getOptionDisabled={(option) => {
                    if (!filePreview?.tags) return false;
                    return (
                        filePreview?.tags.filter((t) => t === option).length > 0
                    );
                }}
                renderInput={(params) => (
                    <TextField
                        {...params}
                        autoFocus
                        label={t("tags.tagDialogInputPlaceholder")}
                    />
                )}
            />
        </DialogBase>
    );
};
