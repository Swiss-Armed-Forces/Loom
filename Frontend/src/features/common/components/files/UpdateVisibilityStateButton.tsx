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
    const [showDialog, setShowDialog] = useState(false);

    const handleIconClick = () => {
        if (file_id) {
            updateSingleFile();
        } else {
            setShowDialog(true);
        }
    };

    const updateSingleFile = async () => {
        if (!searchQuery || !file_id) return;

        try {
            dispatch(startLoadingIndicator());
            await updateFile(file_id, !fileHidden);

            const successMessage = fileHidden
                ? t("updateFileState.scheduledShowFileToast")
                : t("updateFileState.scheduledHideFileToast");
            toast.success(successMessage);
        } catch (err) {
            toast.error(t("updateFileState.scheduledErrorToast", { err }));
        } finally {
            dispatch(stopLoadingIndicator());
        }
    };

    const updateMultipleFiles = async (shouldHide: boolean) => {
        if (!searchQuery) return;

        try {
            dispatch(startLoadingIndicator());
            setShowDialog(false);
            await updateFiles(searchQuery, shouldHide);

            const successMessage = shouldHide
                ? t("updateFileState.scheduledHideFilesToast")
                : t("updateFileState.scheduledShowFilesToast");
            toast.success(successMessage);
        } catch (err) {
            toast.error(t("updateFileState.scheduledErrorToast", { err }));
        } finally {
            dispatch(stopLoadingIndicator());
        }
    };

    const handleClose = (_: unknown, reason: string) => {
        if (reason === "backdropClick") return;
        setShowDialog(false);
    };

    const VisibilityIcon = fileHidden ? Visibility : VisibilityOff;
    const iconColor = colorSecondary ? "secondary" : undefined;
    const iconTitle = fileHidden
        ? t("updateFileState.show")
        : t("updateFileState.hide");

    if (icon_only) {
        return (
            <>
                <IconButton
                    onClick={handleIconClick}
                    disabled={disabled}
                    title={iconTitle}
                >
                    <VisibilityIcon color={iconColor} />
                </IconButton>
                {!file_id && (
                    <UpdateVisibilityDialog
                        open={showDialog}
                        onClose={handleClose}
                        onCancel={() => setShowDialog(false)}
                        onShow={() => updateMultipleFiles(false)}
                        onHide={() => updateMultipleFiles(true)}
                        numberOfResults={numberOfResults}
                    />
                )}
            </>
        );
    }

    return (
        <>
            <Button
                onClick={() => setShowDialog(true)}
                color="secondary"
                disabled={disabled}
                variant={button_full_width ? "contained" : "text"}
                startIcon={button_full_width ? <VisibilityOff /> : null}
                fullWidth={button_full_width}
            >
                <span className="btn-label">
                    {t("updateFileState.openDialog")}
                </span>
            </Button>
            <UpdateVisibilityDialog
                open={showDialog}
                onClose={handleClose}
                onCancel={() => setShowDialog(false)}
                onShow={() => updateMultipleFiles(false)}
                onHide={() => updateMultipleFiles(true)}
                numberOfResults={numberOfResults}
            />
        </>
    );
}

interface UpdateVisibilityDialogProps {
    open: boolean;
    onClose: (event: unknown, reason: string) => void;
    onCancel: () => void;
    onShow: () => void;
    onHide: () => void;
    numberOfResults: number;
}

function UpdateVisibilityDialog({
    open,
    onClose,
    onCancel,
    onShow,
    onHide,
    numberOfResults,
}: UpdateVisibilityDialogProps) {
    return (
        <Dialog open={open} fullWidth onClose={onClose}>
            <DialogTitle>
                {t("updateFileState.dialog.title")}
                <IconButton
                    aria-label="close"
                    onClick={onCancel}
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
                    onClick={onCancel}
                >
                    {t("common.cancel")}
                </Button>
                <Button
                    startIcon={<Visibility />}
                    onClick={onShow}
                    color="primary"
                    variant="contained"
                >
                    {t("updateFileState.showFiles")}
                </Button>
                <Button
                    startIcon={<VisibilityOff />}
                    onClick={onHide}
                    color="primary"
                    variant="contained"
                >
                    {t("updateFileState.hideFiles")}
                </Button>
            </DialogActions>
        </Dialog>
    );
}
