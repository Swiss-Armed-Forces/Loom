import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
} from "@mui/material";
import { Close } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

interface ConfirmationDialogProps {
    open: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    message: string;
    confirmButtonText: string;
    cancelButtonText: string;
}

export function ConfirmationDialog({
    open,
    onClose,
    onConfirm,
    title,
    message,
    confirmButtonText,
    cancelButtonText,
}: ConfirmationDialogProps) {
    const { t } = useTranslation();

    const handleClose = (_: unknown, reason: string) => {
        if (reason && reason === "backdropClick") {
            return;
        }
        onClose();
    };

    return (
        <Dialog open={open} fullWidth={true} onClose={handleClose}>
            <DialogTitle>
                {title}
                <IconButton
                    aria-label="close"
                    onClick={onClose}
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
                <div>{message}</div>
            </DialogContent>
            <DialogActions>
                <Button
                    startIcon={<Close />}
                    variant="outlined"
                    color="secondary"
                    onClick={onClose}
                >
                    {cancelButtonText}
                </Button>
                <Button variant="contained" color="primary" onClick={onConfirm}>
                    {confirmButtonText}
                </Button>
            </DialogActions>
        </Dialog>
    );
}
