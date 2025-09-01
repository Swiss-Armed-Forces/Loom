import { Close, Translate, TranslateOutlined } from "@mui/icons-material";
import {
    Autocomplete,
    Box,
    Button,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    TextField,
    Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import styles from "./SearchTranslateDialog.module.css";
import { t } from "i18next";
import { updateQuery, selectLanguages, selectQuery } from "../searchSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { LibretranslateSupportedLanguages } from "../../../app/api";

export function SearchTranslateDialog() {
    const dispatch = useAppDispatch();
    const [open, setOpen] = useState<boolean>(false);
    const searchQuery = useAppSelector(selectQuery);
    const languages = useAppSelector(selectLanguages);
    const [searchTranslationLanguage, setSearchTranslationLanguage] = useState<
        LibretranslateSupportedLanguages[]
    >([]);

    useEffect(() => {
        if (!searchQuery) return;
        setSearchTranslationLanguage(searchQuery.languages ?? []);
    }, [searchQuery]);

    const handleClose = (_: unknown, reason: string = "") => {
        if (reason && reason == "backdropClick") {
            return;
        }
        setOpen(false);
    };

    const save = () => {
        dispatch(
            updateQuery({
                ...searchQuery,
                languages: searchTranslationLanguage,
            }),
        );
        setOpen(false);
    };

    return (
        <>
            {searchQuery?.languages?.map((item) => (
                <Chip
                    key={item.code}
                    label={item.code}
                    size="small"
                    onClick={() => {}}
                    onDelete={() => {
                        const updated =
                            searchQuery.languages?.filter(
                                (lang) => lang.code !== item.code,
                            ) ?? [];

                        dispatch(
                            updateQuery({
                                ...searchQuery,
                                languages: updated,
                            }),
                        );
                    }}
                    style={{
                        backgroundColor: "#fff",
                    }}
                />
            ))}
            <IconButton
                className={styles.icon}
                title="Translate"
                onClick={() => setOpen(true)}
            >
                <Translate />
            </IconButton>
            <Dialog open={open} fullWidth={true} onClose={handleClose}>
                <DialogTitle>
                    <Typography>{t("translateFilesDialog.title")}</Typography>
                    <IconButton
                        aria-label="close"
                        onClick={() => setOpen(false)}
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
                        className={styles.autocompleteField}
                        options={languages ?? []}
                        value={searchTranslationLanguage}
                        multiple={true}
                        isOptionEqualToValue={(option, value) =>
                            option.code === value.code
                        }
                        onChange={(
                            _e,
                            value: LibretranslateSupportedLanguages[] | null,
                        ) => setSearchTranslationLanguage(value ?? [])}
                        getOptionLabel={(option) => option.name}
                        renderOption={(props, option) => (
                            <Box component="li" {...props}>
                                {option.name}
                            </Box>
                        )}
                        renderInput={(params) => (
                            <TextField
                                {...params}
                                label={t(
                                    "translateFilesDialog.languageInputTo",
                                )}
                            />
                        )}
                    ></Autocomplete>
                </DialogContent>
                <DialogActions>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        onClick={() => handleClose(null)}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        startIcon={<TranslateOutlined />}
                        onClick={() => save()}
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
