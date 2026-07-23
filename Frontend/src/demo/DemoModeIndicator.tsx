import { Close } from "@mui/icons-material";
import {
    Dialog,
    DialogContent,
    DialogTitle,
    IconButton,
    Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import styles from "./DemoModeIndicator.module.css";

export const DemoModeIndicator = () => {
    const [open, setOpen] = useState(false);
    const { t } = useTranslation();

    return (
        <>
            <div className={styles.spacer} aria-hidden="true" />
            <div className={styles.corner}>
                <button
                    className={styles.ribbon}
                    type="button"
                    aria-haspopup="dialog"
                    aria-expanded={open}
                    aria-controls="demo-mode-dialog"
                    onClick={() => setOpen(true)}
                >
                    {t("demoMode.indicator")}
                </button>
            </div>
            <Dialog
                id="demo-mode-dialog"
                open={open}
                fullWidth
                maxWidth="xs"
                onClose={() => setOpen(false)}
                aria-labelledby="demo-mode-dialog-title"
            >
                <DialogTitle id="demo-mode-dialog-title">
                    {t("demoMode.title")}
                    <IconButton
                        aria-label={t("common.close")}
                        title={t("common.close")}
                        onClick={() => setOpen(false)}
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
                <DialogContent dividers>
                    <Typography>{t("demoMode.description")}</Typography>
                </DialogContent>
            </Dialog>
        </>
    );
};
