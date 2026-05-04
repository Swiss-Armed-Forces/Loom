import { Close, TranslateOutlined } from "@mui/icons-material";
import { Autocomplete, Box, Button, TextField } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
    LibretranslateSupportedLanguages,
    scheduleFileTranslation,
    scheduleSingleFileTranslation,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    DialogProps,
    setBackgroundTaskSpinnerActive,
} from "@app/slices/commonSlice";
import { selectLanguages } from "@app/slices/searchSlice";
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
    fileId,
    searchQuery,
}: TranslationDialogProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const languages = useAppSelector(selectLanguages);
    const [language, setLanguage] =
        useState<LibretranslateSupportedLanguages | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const startTranslation = async () => {
        if (!searchQuery || !language) return;

        setIsLoading(true);
        dispatch(setBackgroundTaskSpinnerActive());
        try {
            if (fileId) {
                await scheduleSingleFileTranslation(language.code, fileId);
            } else {
                await scheduleFileTranslation(language.code, searchQuery);
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
                        disabled={!language || isLoading}
                    >
                        {t("translateFilesDialog.executeButton")}
                    </Button>
                </>
            }
        >
            <Autocomplete
                className={styles.addTranslationDialogContent}
                options={languages ?? []}
                value={language}
                multiple={false}
                autoHighlight
                isOptionEqualToValue={(option, value) =>
                    option.code === value.code
                }
                onChange={(_e, value) => setLanguage(value)}
                getOptionLabel={(option) => option.name}
                renderOption={(props, option) => {
                    const { key, ...otherProps } = props;
                    return (
                        <Box component="li" key={key} {...otherProps}>
                            {option.name}
                        </Box>
                    );
                }}
                renderInput={(params) => (
                    <TextField
                        {...params}
                        autoFocus
                        label={t("translateFilesDialog.languageInput")}
                    />
                )}
            />
        </DialogBase>
    );
};
