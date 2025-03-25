import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import { Close } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { IconButton, Typography } from "@mui/material";
import * as React from "react";

interface ConfirmDialogProps {
    open: boolean;
    text: string;
    buttonText: string;
    handleConfirmation: () => void;
    cancel: () => void;
    icon: React.ReactNode;
}

export function ConfirmDialog({
    open,
    text,
    buttonText,
    handleConfirmation,
    cancel,
    icon,
}: ConfirmDialogProps) {
    const { t } = useTranslation();

    const handleClose = (_: unknown, reason: string) => {
        if (reason && reason == "backdropClick") {
            return;
        }
        cancel();
    };

    return (
        <Dialog open={open} onClose={handleClose}>
            <DialogTitle>
                <Typography>{t("confirmDialog.title")}</Typography>
                <IconButton
                    aria-label="close"
                    onClick={cancel}
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
                <div>{text}</div>
            </DialogContent>
            <DialogActions>
                <Button
                    startIcon={<Close />}
                    variant="outlined"
                    color="secondary"
                    onClick={cancel}
                >
                    {t("common.cancel")}
                </Button>
                <Button
                    startIcon={icon}
                    variant="contained"
                    onClick={handleConfirmation}
                >
                    {buttonText}
                </Button>
            </DialogActions>
        </Dialog>
    );
}
