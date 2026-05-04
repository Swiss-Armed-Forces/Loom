import { YoutubeSearchedForOutlined } from "@mui/icons-material";
import { Close } from "@mui/icons-material";
import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { scheduleFileIndexing, scheduleSingleFileIndexing } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { setBackgroundTaskSpinnerActive } from "@app/slices/commonSlice";
import { selectQuery, selectTotalFiles } from "@app/slices/searchSlice";

interface ReIndexProps {
    fileId?: string;
    disabled?: boolean;
    iconOnly?: boolean;
}

export const ReIndexButton = ({
    fileId,
    disabled = false,
    iconOnly = false,
}: ReIndexProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const [showDialog, setShowDialog] = useState(false);
    const filesCount = useAppSelector(selectTotalFiles);

    const handleReindex = () => {
        if (!searchQuery && !fileId) return;
        dispatch(setBackgroundTaskSpinnerActive());
        let result: Promise<void>;
        if (fileId) {
            result = scheduleSingleFileIndexing(fileId);
        } else if (searchQuery) {
            result = scheduleFileIndexing(searchQuery);
        } else {
            toast.error("Error while opening Dialog: No File or Query found");
            return;
        }

        result
            .then(() => {
                toast.success(
                    "Re-indexing successfully scheduled, this might take a while.",
                );
            })
            .catch((err) => {
                toast.error(
                    "Cannot re-index files. Code: " +
                        err.status +
                        ", Text: " +
                        err.text,
                );
            });
        setShowDialog(false);
    };

    const startReindexProcess = () => {
        if ((!searchQuery && !fileId) || filesCount === 0) return;
        if (fileId) {
            // For single files, skip dialog and reindex directly
            handleReindex();
        } else {
            // For multiple files, show confirmation dialog
            setShowDialog(true);
        }
    };

    const handleCloseDialog = (_: unknown, reason: string) => {
        if (reason && reason === "backdropClick") {
            return;
        }
        setShowDialog(false);
    };

    return (
        <>
            {fileId || iconOnly ? (
                <IconButton
                    onClick={() => {
                        startReindexProcess();
                    }}
                    disabled={disabled}
                    title="Re-index"
                    aria-label="re-index"
                >
                    <YoutubeSearchedForOutlined />
                </IconButton>
            ) : (
                <Button
                    onClick={() => {
                        startReindexProcess();
                    }}
                    disabled={disabled}
                    color="secondary"
                    fullWidth={true}
                    variant={"contained"}
                    startIcon={<YoutubeSearchedForOutlined />}
                >
                    <span className="btn-label">
                        {t("sideMenu.reIndexQueriedFiles")}
                    </span>
                </Button>
            )}
            <Dialog
                open={showDialog}
                fullWidth={true}
                onClose={handleCloseDialog}
            >
                <DialogTitle>
                    {t("reIndex.confirmationTitle")}
                    <IconButton
                        aria-label="close"
                        onClick={() => {
                            setShowDialog(false);
                        }}
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
                    <p>
                        {t("reIndex.confirmationMessage", {
                            count: filesCount,
                        })}
                    </p>
                </DialogContent>
                <DialogActions>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        onClick={() => {
                            setShowDialog(false);
                        }}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        startIcon={<YoutubeSearchedForOutlined />}
                        onClick={handleReindex}
                        color="primary"
                        variant="contained"
                    >
                        {t("reIndex.executeButton")}
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
};
