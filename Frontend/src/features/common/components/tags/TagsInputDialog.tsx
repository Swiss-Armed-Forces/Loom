import { Close, LabelOutlined } from "@mui/icons-material";
import {
    Autocomplete,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    LinearProgress,
    TextField,
} from "@mui/material";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { useAppDispatch, useAppSelector } from "../../../../app/hooks.ts";

import {
    ActionType,
    selectAction,
    setAction,
    selectFileDetailData,
    selectQuery,
    selectTags,
    setFilePreview,
} from "../../../search/searchSlice.ts";
import { setBackgroundTaskSpinnerActive } from "../../commonSlice.ts";
import {
    ResponseError,
    addTagsToFile,
    addTagsToFiles,
} from "../../../../app/api";

export function TagsInputDialog() {
    const fileDetailData = useAppSelector(selectFileDetailData);
    const action = useAppSelector(selectAction);
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
        try {
            dispatch(setBackgroundTaskSpinnerActive());
            setIsLoading(true);
            // Maybe fileDetailData.filePreview && fileDetailData.searchQuery
            if (fileDetailData.filePreview?.fileId) {
                await addTagsToFile(
                    fileDetailData.filePreview?.fileId,
                    selectedTagsToAdd,
                );

                // Save tags locally
                dispatch(
                    setFilePreview({
                        ...fileDetailData.filePreview,
                        tags: [
                            ...new Set([
                                ...(fileDetailData.filePreview?.tags ?? []),
                                ...selectedTagsToAdd,
                            ]),
                        ],
                    }),
                );
            } else {
                await addTagsToFiles(searchQuery, selectedTagsToAdd);
            }
            toast.success(t("tags.scheduledToast"));
        } catch (error: any) {
            toast.error(
                t("tags.scheduledErrorToast", {
                    err: await getErrorMessage(error),
                }),
            );
        } finally {
            setIsLoading(false);
            handleClose();
        }
    };

    const handleClose = useCallback(() => {
        dispatch(setAction(ActionType.SEARCH));
    }, [dispatch]);

    // dialog not open: don't render dom element
    if (action != ActionType.TAGS) return;

    return (
        <Dialog open fullWidth={true} onClose={handleClose}>
            <DialogTitle>
                {t("tags.tagDialogTitle")}
                <IconButton
                    aria-label="close"
                    onClick={handleClose}
                    title={t("common.close")}
                    sx={{
                        position: "absolute",
                        right: 8,
                        top: 8,
                        color: (theme) => theme.palette.grey[500],
                    }}
                >
                    <Close />
                </IconButton>
            </DialogTitle>
            <DialogContent>
                <p>{t("tags.tagDialogHint")}</p>
                <Autocomplete
                    autoSelect
                    freeSolo
                    multiple
                    options={existingTags}
                    onChange={(_e, value) => setSelectedTagsToAdd(value)}
                    getOptionDisabled={(option) => {
                        if (!fileDetailData.filePreview?.tags) return false;
                        return (
                            fileDetailData.filePreview?.tags.filter(
                                (t) => t === option,
                            ).length > 0
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
            </DialogContent>
            <DialogActions>
                <Button
                    startIcon={<Close />}
                    variant="outlined"
                    color="secondary"
                    tabIndex={2}
                    onClick={handleClose}
                >
                    {t("common.cancel")}
                </Button>
                <Button
                    onClick={startPersisting}
                    disabled={selectedTagsToAdd.length === 0}
                    color="primary"
                    variant="contained"
                    startIcon={<LabelOutlined />}
                    tabIndex={1}
                >
                    {t("tags.tagDialogSubmit")}
                </Button>
            </DialogActions>
            {isLoading && (
                <div className="loadingIndicator">
                    <LinearProgress color="primary" />
                </div>
            )}
            {!isLoading && <div className="loadingIndicatorPlaceholder"></div>}
        </Dialog>
    );
}
