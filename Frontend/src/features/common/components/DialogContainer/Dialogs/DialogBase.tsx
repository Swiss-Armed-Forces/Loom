import { Close } from "@mui/icons-material";
import {
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    LinearProgress,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { DialogProps } from "@app/slices/commonSlice";

interface DialogBaseProps extends DialogProps {
    title: string;
    actions?: React.ReactNode;
    children: React.ReactNode;
    loading?: boolean;
}

export const DialogBase = ({
    id,
    onClose,
    title,
    actions,
    children,
    loading = false,
}: DialogBaseProps) => {
    const { t } = useTranslation();

    return (
        <Dialog
            open
            fullWidth
            onClose={onClose}
            aria-labelledby={`dialog-${id}`}
            id={id}
        >
            <DialogTitle>
                {title}
                <IconButton
                    aria-label="close"
                    title={t("common.close")}
                    onClick={onClose}
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

            <DialogContent dividers>{children}</DialogContent>

            {actions && <DialogActions>{actions}</DialogActions>}

            {loading ? (
                <LinearProgress
                    color="primary"
                    sx={{ position: "absolute", bottom: 0, left: 0, right: 0 }}
                />
            ) : (
                // Maintain layout height to prevent "jumping" when loading starts/stops
                <div style={{ height: "4px" }} />
            )}
        </Dialog>
    );
};
