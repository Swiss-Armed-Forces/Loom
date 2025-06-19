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
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { useAppDispatch, useAppSelector } from "../../../../app/hooks.ts";

import { selectQuery, selectTags } from "../../../search/searchSlice.ts";
import LabelIcon from "@mui/icons-material/Label";
import { setBackgroundTaskSpinnerActive } from "../../commonSlice.ts";
import { addTagToFile, addTagsToFiles } from "../../../../app/api";
interface TagsInputProps {
    tagsAlreadyAssignedToFile?: string[];
    file_id?: string;
    button_full_width?: boolean;
    disabled?: boolean;
    icon_only?: boolean;
}

export function TagsInput({
    tagsAlreadyAssignedToFile,
    file_id,
    button_full_width = false,
    disabled = false,
    icon_only = false,
}: TagsInputProps) {
    const searchQuery = useAppSelector(selectQuery);
    const existingTags = useAppSelector(selectTags);
    const [showAddTagDialog, setShowAddTagDialog] = useState(false);
    const [selectedTagsToAdd, setSelectedTagsToAdd] = useState<string[]>([]);
    const { t } = useTranslation();
    const [loadingBar, setLoadingBar] = useState(false);
    const dispatch = useAppDispatch();

    const startPersisting = async () => {
        if (!searchQuery) return;
        try {
            dispatch(setBackgroundTaskSpinnerActive());
            setLoadingBar(true);
            if (file_id) {
                for (const tag of selectedTagsToAdd) {
                    await addTagToFile(file_id, tag);
                }
            } else {
                await addTagsToFiles(searchQuery, selectedTagsToAdd);
            }
            toast.success(t("tags.scheduledToast"));
        } catch (err) {
            toast.error(
                t("tags.scheduledErrorToast", {
                    err: err,
                }),
            );
        } finally {
            setLoadingBar(false);
            setShowAddTagDialog(false);
        }
    };

    const handleCloseDialog = (_: unknown, reason: string) => {
        if (reason && reason == "backdropClick") {
            return;
        }
        setShowAddTagDialog(false);
    };

    const addTagsToAdd = (newTags: string[]) => {
        const tags = newTags.map((t) =>
            /* filter out characters with semantic meaning within ES query */
            t.replaceAll(/[ ()\\:]/g, "-"),
        );
        setSelectedTagsToAdd(tags);
    };

    return (
        <>
            {icon_only ? (
                <IconButton
                    onClick={() => setShowAddTagDialog(true)}
                    disabled={disabled}
                    title={t("tags.addTag")}
                >
                    <LabelIcon></LabelIcon>
                </IconButton>
            ) : (
                <Button
                    onClick={() => setShowAddTagDialog(true)}
                    disabled={disabled}
                    color="secondary"
                    variant={button_full_width ? "contained" : "text"}
                    startIcon={button_full_width ? <LabelOutlined /> : null}
                    fullWidth={button_full_width}
                >
                    <span className="btn-label">{t("tags.addTag")}</span>
                </Button>
            )}
            <Dialog
                open={showAddTagDialog}
                fullWidth={true}
                onClose={handleCloseDialog}
            >
                <DialogTitle>
                    {t("tags.tagDialogTitle")}
                    <IconButton
                        aria-label="close"
                        onClick={() => setShowAddTagDialog(false)}
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
                        onChange={(_e, value) => addTagsToAdd(value)}
                        getOptionDisabled={(option) => {
                            if (!tagsAlreadyAssignedToFile) return false;
                            return (
                                tagsAlreadyAssignedToFile.filter(
                                    (t) => t === option,
                                ).length > 0
                            );
                        }}
                        renderInput={(params) => (
                            <TextField
                                {...params}
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
                        onClick={() => {
                            setShowAddTagDialog(false);
                        }}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        onClick={startPersisting}
                        disabled={selectedTagsToAdd.length === 0}
                        color="primary"
                        variant="contained"
                        startIcon={<LabelOutlined />}
                    >
                        {t("tags.tagDialogSubmit")}
                    </Button>
                </DialogActions>
                {loadingBar && (
                    <div className="loadingIndicator">
                        <LinearProgress color="primary" />
                    </div>
                )}
                {!loadingBar && (
                    <div className="loadingIndicatorPlaceholder"></div>
                )}
            </Dialog>
        </>
    );
}
