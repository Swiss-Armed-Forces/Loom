import { useState } from "react";
import { Close, Translate, TranslateOutlined } from "@mui/icons-material";
import {
    Autocomplete,
    Box,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    TextField,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { useAppSelector, useAppDispatch } from "../../../app/hooks";
import {
    LibretranslateSupportedLanguages,
    scheduleFileTranslation,
    scheduleSingleFileTranslation,
} from "../../../app/api";
import {
    selectTranslationLanguage,
    selectQuery,
    selectLanguages,
    setTranslationLanguage,
} from "../searchSlice";
import styles from "./TranslationDialog.module.css";
import { setBackgroundTaskSpinnerActive } from "../../common/commonSlice.ts";

interface TranslationProps {
    file_id?: string;
    disabled?: boolean;
    icon_only?: boolean;
}

export function TranslationDialog({
    file_id,
    disabled = false,
    icon_only = false,
}: TranslationProps) {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const languages = useAppSelector(selectLanguages);
    const translationLanguage = useAppSelector(selectTranslationLanguage);
    const [showTranslationDialog, setShowTranslationDialog] = useState(false);

    const startFileTranslation = async () => {
        if (!searchQuery) return;
        if (!translationLanguage) return;

        dispatch(setBackgroundTaskSpinnerActive());
        try {
            if (file_id) {
                await scheduleSingleFileTranslation(
                    translationLanguage.code,
                    file_id,
                );
            } else {
                await scheduleFileTranslation(
                    translationLanguage.code,
                    searchQuery,
                );
            }
            toast.success(t("translateFilesDialog.scheduledToast"));
        } catch (err) {
            toast.error(
                t("translateFilesDialog.scheduledErrorToast", {
                    err: err,
                }),
            );
        }
        setShowTranslationDialog(false);
    };

    const handleClose = (_: unknown, reason: string) => {
        if (reason && reason == "backdropClick") {
            return;
        }
        setShowTranslationDialog(false);
    };

    return (
        <>
            {file_id || icon_only ? (
                <IconButton
                    onClick={() => setShowTranslationDialog(true)}
                    disabled={disabled}
                    title="Translate"
                    aria-label="translate"
                >
                    <Translate />
                </IconButton>
            ) : (
                <Button
                    onClick={() => setShowTranslationDialog(true)}
                    disabled={disabled}
                    color="secondary"
                    fullWidth={true}
                    variant={"contained"}
                    startIcon={<Translate />}
                >
                    <span className="btn-label">
                        {t("sideMenu.translateQueriedFiles")}
                    </span>
                </Button>
            )}
            <Dialog
                open={showTranslationDialog}
                fullWidth={true}
                onClose={handleClose}
            >
                <DialogTitle>
                    {t("translateFilesDialog.title")}
                    <IconButton
                        aria-label="close"
                        onClick={() => setShowTranslationDialog(false)}
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
                    <Autocomplete
                        className={styles.addTranslationDialogContent}
                        options={languages ?? []}
                        defaultValue={translationLanguage}
                        multiple={false}
                        freeSolo={false}
                        isOptionEqualToValue={(option, value) =>
                            option.code === value.code
                        }
                        onChange={(
                            _e,
                            value: LibretranslateSupportedLanguages | null,
                        ) => dispatch(setTranslationLanguage(value))}
                        getOptionLabel={(option) => option.name}
                        renderOption={(props, option) => {
                            // eslint-disable-next-line react/prop-types
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
                                label={t("translateFilesDialog.languageInput")}
                            />
                        )}
                    ></Autocomplete>
                </DialogContent>
                <DialogActions>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        onClick={() => {
                            setShowTranslationDialog(false);
                        }}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        startIcon={<TranslateOutlined />}
                        onClick={startFileTranslation}
                        color="primary"
                        variant="contained"
                    >
                        {t("translateFilesDialog.executeButton")}
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
}
