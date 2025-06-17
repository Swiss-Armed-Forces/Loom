import { Close, Visibility, VisibilityOff } from "@mui/icons-material";
import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
} from "@mui/material";
import { t } from "i18next";
import { selectTotalFiles, selectQuery } from "../../../search/searchSlice";
import { useAppDispatch, useAppSelector } from "../../../../app/hooks";
import { toast } from "react-toastify";
import { useState } from "react";
import { updateFile, updateFiles } from "../../../../app/api";
import { startLoadingIndicator, stopLoadingIndicator } from "../../commonSlice";

interface UpdateVisibilityStateInputProps {
    file_id?: string;
    button_full_width?: boolean;
    disabled?: boolean;
    icon_only?: boolean;
    fileHidden?: boolean;
    colorSecondary?: boolean;
}

export function UpdateVisibilityButton({
    file_id,
    button_full_width = false,
    disabled = false,
    fileHidden = false,
    icon_only = false,
    colorSecondary = false,
}: UpdateVisibilityStateInputProps) {
    const dispatch = useAppDispatch();
    const numberOfResults = useAppSelector(selectTotalFiles);
    const searchQuery = useAppSelector(selectQuery);
    const [showUpdateFileStateDialog, setUpdateFileStateDialog] =
        useState(false);

    const startPersistingFile = async () => {
        if (!searchQuery) return;
        if (!file_id) return;
        try {
            dispatch(startLoadingIndicator());
            await updateFile(file_id, !fileHidden);
            if (fileHidden) {
                toast.success(t("updateFileState.scheduledShowFileToast"));
            } else {
                toast.success(t("updateFileState.scheduledHideFileToast"));
            }
        } catch (err) {
            toast.error(
                t("updateFileState.scheduledErrorToast", {
                    err: err,
                }),
            );
        } finally {
            dispatch(stopLoadingIndicator());
        }
    };

    const startPersistingFiles = async () => {
        if (!searchQuery) return;
        try {
            dispatch(startLoadingIndicator());
            setUpdateFileStateDialog(false);
            await updateFiles(searchQuery, !fileHidden);
            if (fileHidden) {
                toast.success(t("updateFileState.scheduledShowFilesToast"));
            } else {
                toast.success(t("updateFileState.scheduledHideFilesToast"));
            }
        } catch (err) {
            toast.error(
                t("updateFileState.scheduledErrorToast", {
                    err: err,
                }),
            );
        } finally {
            dispatch(stopLoadingIndicator());
        }
    };

    const handleClose = (_: unknown, reason: string) => {
        if (reason && reason == "backdropClick") {
            return;
        }
        setUpdateFileStateDialog(false);
    };

    return (
        <>
            {icon_only ? (
                fileHidden ? (
                    <IconButton
                        onClick={() => startPersistingFile()}
                        disabled={disabled}
                        title={t("updateFileState.show")}
                    >
                        {colorSecondary ? (
                            <Visibility color="secondary" />
                        ) : (
                            <Visibility />
                        )}
                    </IconButton>
                ) : (
                    <IconButton
                        onClick={() => startPersistingFile()}
                        disabled={disabled}
                        title={t("updateFileState.hide")}
                    >
                        {colorSecondary ? (
                            <VisibilityOff color="secondary" />
                        ) : (
                            <VisibilityOff />
                        )}
                    </IconButton>
                )
            ) : (
                <>
                    <Button
                        onClick={() => setUpdateFileStateDialog(true)}
                        color="secondary"
                        disabled={disabled}
                        variant={button_full_width ? "contained" : "text"}
                        startIcon={button_full_width ? <Visibility /> : null}
                        fullWidth={button_full_width}
                    >
                        <span className="btn-label">
                            {t("updateFileState.openDialog")}
                        </span>
                    </Button>
                    <Dialog
                        open={showUpdateFileStateDialog}
                        fullWidth={true}
                        onClose={handleClose}
                    >
                        <DialogTitle>
                            {t("updateFileState.dialog.title")}
                            <IconButton
                                aria-label="close"
                                onClick={() => setUpdateFileStateDialog(false)}
                                title={t("common.close")}
                                sx={{
                                    position: "absolute",
                                    right: 8,
                                    top: 8,
                                }}
                            >
                                <Close />
                            </IconButton>
                        </DialogTitle>
                        <DialogContent>
                            <div>
                                {t("updateFileState.dialog.text", {
                                    numberOfResults: numberOfResults.toString(),
                                })}
                            </div>
                        </DialogContent>
                        <DialogActions>
                            <Button
                                startIcon={<Close />}
                                variant="outlined"
                                color="secondary"
                                onClick={() => {
                                    setUpdateFileStateDialog(false);
                                }}
                            >
                                {t("common.cancel")}
                            </Button>
                            <Button
                                startIcon={<Visibility />}
                                onClick={() => {
                                    fileHidden = true;
                                    startPersistingFiles();
                                }}
                                color="primary"
                                variant="contained"
                            >
                                {t("updateFileState.showFiles")}
                            </Button>
                            <Button
                                startIcon={<VisibilityOff />}
                                onClick={() => {
                                    fileHidden = false;
                                    startPersistingFiles();
                                }}
                                color="primary"
                                variant="contained"
                            >
                                {t("updateFileState.hideFiles")}
                            </Button>
                        </DialogActions>
                    </Dialog>
                </>
            )}
        </>
    );
}
