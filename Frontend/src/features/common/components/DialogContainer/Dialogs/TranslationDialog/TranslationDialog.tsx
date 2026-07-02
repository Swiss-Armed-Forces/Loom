import { Close, TranslateOutlined } from "@mui/icons-material";
import { Button, TextField } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
    scheduleFileTranslation,
    scheduleSingleFileTranslation,
} from "@app/api";
import { useAppDispatch } from "@app/hooks";
import {
    DialogProps,
    setBackgroundTaskSpinnerActive,
} from "@app/slices/commonSlice";
import { SearchQuery } from "@features/common/utils/model";

import { DialogBase } from "..";

import styles from "./TranslationDialog.module.css";

interface TranslationDialogProps extends DialogProps {
    fileId?: string;
    searchQuery: SearchQuery;
}

export const TranslationDialog = ({
    id,
    onClose,
    isTop,
    fileId,
    searchQuery,
}: TranslationDialogProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const [languageCode, setLanguageCode] = useState<string>("");
    const [isLoading, setIsLoading] = useState(false);

    const startTranslation = async () => {
        if (!searchQuery || !languageCode.trim()) return;

        setIsLoading(true);
        dispatch(setBackgroundTaskSpinnerActive());
        try {
            if (fileId) {
                await scheduleSingleFileTranslation(
                    languageCode.trim(),
                    fileId,
                );
            } else {
                await scheduleFileTranslation(languageCode.trim(), searchQuery);
            }
            toast.success(t("translateFilesDialog.scheduledToast"));
            onClose();
        } catch (err) {
            toast.error(t("translateFilesDialog.scheduledErrorToast", { err }));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <DialogBase
            id={id}
            onClose={onClose}
            isTop={isTop}
            title={t("translateFilesDialog.title")}
            loading={isLoading}
            actions={
                <>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        onClick={onClose}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        startIcon={<TranslateOutlined />}
                        onClick={startTranslation}
                        color="primary"
                        variant="contained"
                        disabled={!languageCode.trim() || isLoading}
                    >
                        {t("translateFilesDialog.executeButton")}
                    </Button>
                </>
            }
        >
            <TextField
                className={styles.addTranslationDialogContent}
                autoFocus
                label={t("translateFilesDialog.languageInput")}
                value={languageCode}
                onChange={(e) => setLanguageCode(e.target.value)}
                placeholder="e.g. en, de, fr"
            />
        </DialogBase>
    );
};
