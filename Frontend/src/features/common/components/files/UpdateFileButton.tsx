import { Close } from "@mui/icons-material";
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
import {
    updateFile,
    UpdateFileRequest,
    updateFiles,
} from "../../../../app/api";
import { startLoadingIndicator, stopLoadingIndicator } from "../../commonSlice";
import {
    UpdateFileDialogAction,
    UpdateFileButtonProps,
    UpdateFileProperty,
} from "./UpdateFileButton.types";

interface UpdateFileDialogProps {
    open: boolean;
    numberOfResults: number;
    onClose: (event: unknown, reason: string) => void;
    onCancel: () => void;
    actions: UpdateFileDialogAction[];
    property: UpdateFileProperty;
}

export function UpdateFileButton({
    file_id,
    button_full_width = false,
    disabled = false,
    icon_only = false,
    icon: Icon,
    iconColor,
    iconTitle,
    actions,
    property,
    successMessage,
    request,
}: UpdateFileButtonProps) {
    const dispatch = useAppDispatch();
    const numberOfResults = useAppSelector(selectTotalFiles);
    const searchQuery = useAppSelector(selectQuery);
    const [showDialog, setShowDialog] = useState(false);
    const dialogActions: UpdateFileDialogAction[] = actions.map((action) => ({
        startIcon: action.startIcon,
        text: action.text,
        onClick: () => updateSingleOrMultipleFiles(action.request),
    }));

    const handleClose = (_: unknown, reason: string) => {
        if (reason === "backdropClick") return;
        setShowDialog(false);
    };

    const handleIconClick = () => {
        if (file_id) {
            updateSingleOrMultipleFiles(request);
        } else {
            setShowDialog(true);
        }
    };

    const updateSingleOrMultipleFiles = async (request: UpdateFileRequest) => {
        if (!file_id && !searchQuery) return;

        try {
            dispatch(startLoadingIndicator());
            if (file_id) {
                await updateFile(file_id, request);
            } else {
                setShowDialog(false);
                // searchQuery will always be != from undefined
                // because if both file_id and searchQuery are false it would exit early
                await updateFiles(searchQuery!, request);
            }

            toast.success(successMessage);
        } catch (err) {
            toast.error(
                t(`updateFileState.${property}.scheduledErrorToast`, { err }),
            );
        } finally {
            dispatch(stopLoadingIndicator());
        }
    };

    if (icon_only) {
        return (
            <>
                <IconButton
                    aria-label={iconTitle}
                    onClick={handleIconClick}
                    disabled={disabled}
                    title={iconTitle}
                >
                    <Icon color={iconColor} />
                </IconButton>
                {!file_id && (
                    <UpdateFileDialog
                        open={showDialog}
                        numberOfResults={numberOfResults}
                        onClose={handleClose}
                        onCancel={() => setShowDialog(false)}
                        actions={dialogActions}
                        property={property}
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
                startIcon={button_full_width ? <Icon /> : null}
                fullWidth={button_full_width}
            >
                <span className="btn-label">
                    {t(`updateFileState.${property}.openDialog`)}
                </span>
            </Button>
            <UpdateFileDialog
                open={showDialog}
                numberOfResults={numberOfResults}
                onClose={handleClose}
                onCancel={() => setShowDialog(false)}
                actions={dialogActions}
                property={property}
            />
        </>
    );
}

function UpdateFileDialog({
    open,
    numberOfResults,
    onClose,
    onCancel,
    actions,
    property,
}: UpdateFileDialogProps) {
    return (
        <Dialog open={open} fullWidth onClose={onClose}>
            <DialogTitle>
                {t(`updateFileState.${property}.dialog.title`)}
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
                    {t(`updateFileState.${property}.dialog.text`, {
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

                {actions.map((action, key) => {
                    const StartIcon = action.startIcon;
                    return (
                        <Button
                            key={key}
                            startIcon={<StartIcon />}
                            onClick={action.onClick}
                            color="primary"
                            variant="contained"
                        >
                            {action.text}
                        </Button>
                    );
                })}
            </DialogActions>
        </Dialog>
    );
}
