import { useCallback, useState } from "react";
import { Close, TranslateOutlined } from "@mui/icons-material";
import {
    Autocomplete,
    Box,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    LinearProgress,
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
    ActionType,
    selectAction,
    setAction,
    selectTranslationLanguage,
    selectQuery,
    selectLanguages,
    setTranslationLanguage,
    selectFileDetailData,
} from "../searchSlice";
import styles from "./TranslationDialog.module.css";
import { setBackgroundTaskSpinnerActive } from "../../common/commonSlice.ts";

export function TranslationDialog() {
    const fileDetailData = useAppSelector(selectFileDetailData);
    const action = useAppSelector(selectAction);
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const languages = useAppSelector(selectLanguages);
    const translationLanguage = useAppSelector(selectTranslationLanguage);
    const [isLoading, setIsLoading] = useState(false);

    const startFileTranslation = async () => {
        if (!searchQuery) return;
        if (!translationLanguage) return;

        dispatch(setBackgroundTaskSpinnerActive());
        try {
            dispatch(setBackgroundTaskSpinnerActive());
            setIsLoading(true);
            if (fileDetailData.filePreview?.fileId) {
                await scheduleSingleFileTranslation(
                    translationLanguage.code,
                    fileDetailData.filePreview?.fileId,
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
        } finally {
            setIsLoading(false);
            handleClose();
        }
    };

    const handleClose = useCallback(() => {
        dispatch(setAction(ActionType.SEARCH));
    }, [dispatch]);

    // dialog not open: don't render dom element
    if (action != ActionType.TRANSLATE) return;

    return (
        <Dialog open fullWidth={true} onClose={handleClose}>
            <DialogTitle>
                {t("translateFilesDialog.title")}
                <IconButton
                    aria-label="close"
                    onClick={handleClose}
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
                <Autocomplete
                    className={styles.addTranslationDialogContent}
                    options={languages ?? []}
                    defaultValue={translationLanguage}
                    multiple={false}
                    freeSolo={false}
                    autoHighlight
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
                            autoFocus
                            label={t("translateFilesDialog.languageInput")}
                        />
                    )}
                />
            </DialogContent>
            <DialogActions>
                <Button
                    startIcon={<Close />}
                    variant="outlined"
                    color="secondary"
                    tabIndex={2}
                    onClick={handleClose}
                >
                    {t("common.cancel")}
                </Button>
                <Button
                    startIcon={<TranslateOutlined />}
                    onClick={startFileTranslation}
                    color="primary"
                    variant="contained"
                    tabIndex={1}
                >
                    {t("translateFilesDialog.executeButton")}
                </Button>
            </DialogActions>
            {isLoading && (
                <div className="loadingIndicator">
                    <LinearProgress color="primary" />
                </div>
            )}
            {!isLoading && <div className="loadingIndicatorPlaceholder"></div>}
        </Dialog>
    );
}
