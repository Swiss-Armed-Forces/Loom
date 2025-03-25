import { useState } from "react";
import {
    Add,
    AttachFile,
    Close,
    Filter1,
    Filter2,
    Filter3,
    Filter4,
    Filter5,
    FindInPage,
    FolderSpecial,
    LocationOn,
    PictureAsPdf,
    Policy,
    Save,
    ScreenSearchDesktop,
    SmartButton,
    Stars,
    Style,
    Tune,
} from "@mui/icons-material";
import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    MenuItem,
    Select,
    TextField,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { useAppDispatch, useAppSelector } from "../../../../app/hooks.ts";
import {
    addCustomQuery,
    initCustomQuery,
    selectQuery,
} from "../../searchSlice.ts";
import styles from "./AddCustomQueryDialog.module.css";

interface TranslationProps {
    disabled?: boolean;
    icon_only?: boolean;
}

// eslint-disable-next-line react-refresh/only-export-components
export const availableCustomQueryIcons = [
    { key: "Tune", icon: <Tune key="Tune" /> },
    { key: "Policy", icon: <Policy key="Policy" /> },
    {
        key: "ScreenSearchDesktop",
        icon: <ScreenSearchDesktop key="ScreenSearchDesktop" />,
    },
    { key: "FindInPage", icon: <FindInPage key="FindInPage" /> },
    { key: "Style", icon: <Style key="Style" /> },
    { key: "FolderSpecial", icon: <FolderSpecial key="FolderSpecial" /> },
    { key: "Stars", icon: <Stars key="Stars" /> },
    { key: "SmartButton", icon: <SmartButton key="SmartButton" /> },
    { key: "LocationOn", icon: <LocationOn key="LocationOn" /> },
    { key: "AttachFile", icon: <AttachFile key="AttachFile" /> },
    { key: "PictureAsPdf", icon: <PictureAsPdf key="PictureAsPdf" /> },
    { key: "Filter1", icon: <Filter1 key="Filter1" /> },
    { key: "Filter2", icon: <Filter2 key="Filter2" /> },
    { key: "Filter3", icon: <Filter3 key="Filter3" /> },
    { key: "Filter4", icon: <Filter4 key="Filter4" /> },
    { key: "Filter5", icon: <Filter5 key="Filter5" /> },
];

export function AddCustomQueryDialog({
    disabled = false,
    icon_only = false,
}: TranslationProps) {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const [showAddCustomQueryDialog, setShowAddCustomQueryDialog] =
        useState(false);

    const [selectedIcon, setSelectedIcon] = useState(
        availableCustomQueryIcons[0]?.key ?? "",
    );
    const [customQueryName, setCustomQueryName] = useState("");

    const addNewCustomQuery = () => {
        if (!searchQuery) return;
        dispatch(
            addCustomQuery(
                initCustomQuery(searchQuery, customQueryName, selectedIcon),
            ),
        );
        setSelectedIcon(availableCustomQueryIcons[0]?.key ?? "");
        setCustomQueryName("");
        setShowAddCustomQueryDialog(false);
    };

    const handleClose = (_: unknown, reason: string) => {
        if (reason && reason == "backdropClick") {
            return;
        }
        setShowAddCustomQueryDialog(false);
    };

    return (
        <>
            {icon_only ? (
                <IconButton
                    sx={{
                        width: "10px",
                        marginLeft: "-4px",
                    }}
                    onClick={() => setShowAddCustomQueryDialog(true)}
                    color="success"
                    disabled={disabled}
                    title={t("sideMenu.savedQueries.saveNew")}
                >
                    <Add
                        sx={{
                            display: "inline-flex",
                            marginLeft: "-12px",
                        }}
                    />
                </IconButton>
            ) : (
                <Button
                    onClick={() => setShowAddCustomQueryDialog(true)}
                    color="success"
                    variant="contained"
                    disabled={disabled}
                    startIcon={<Add />}
                    fullWidth={true}
                >
                    <span className="btn-label">
                        {t("sideMenu.savedQueries.saveNew")}
                    </span>
                </Button>
            )}

            <Dialog
                open={showAddCustomQueryDialog}
                fullWidth={true}
                onClose={handleClose}
            >
                <DialogTitle>
                    {t("addCustomQueryDialog.title")}
                    <IconButton
                        aria-label="close"
                        onClick={() => setShowAddCustomQueryDialog(false)}
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
                    <div className={styles.nameWithIcon}>
                        <Select
                            labelId="custom-query-item-select-label"
                            id="custom-query-item-select"
                            className={styles.customQueryIconSelect}
                            value={selectedIcon}
                            onChange={(e) => {
                                setSelectedIcon(e.target.value);
                            }}
                        >
                            {availableCustomQueryIcons.map((x) => (
                                <MenuItem key={x.key} value={x.key}>
                                    {x.icon}
                                </MenuItem>
                            ))}
                        </Select>
                        <TextField
                            className={styles.customQueryNameInput}
                            id="outlined-basic"
                            label={t("addCustomQueryDialog.nameLabel")}
                            variant="outlined"
                            value={customQueryName}
                            onChange={(event) => {
                                setCustomQueryName(event.target.value);
                            }}
                            required={true}
                        />
                    </div>
                </DialogContent>
                <DialogActions>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        onClick={() => {
                            setCustomQueryName("");
                            setSelectedIcon(
                                availableCustomQueryIcons[0]?.key ?? "",
                            );
                            setShowAddCustomQueryDialog(false);
                        }}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        startIcon={<Save />}
                        onClick={addNewCustomQuery}
                        color="primary"
                        variant="contained"
                        disabled={!customQueryName}
                    >
                        {t("addCustomQueryDialog.add")}
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
}
