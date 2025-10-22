import { useState } from "react";
import { YoutubeSearchedForOutlined } from "@mui/icons-material";
import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { Close } from "@mui/icons-material";
import {
    scheduleFileIndexing,
    scheduleSingleFileIndexing,
} from "../../../app/api";
import { setBackgroundTaskSpinnerActive } from "../../common/commonSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { toast } from "react-toastify";
import { selectQuery, selectTotalFiles, updateQuery } from "../searchSlice";

interface ReIndexProps {
    file_id?: string;
    disabled?: boolean;
    icon_only?: boolean;
}

export function ReIndexButton({
    file_id,
    disabled = false,
    icon_only = false,
}: ReIndexProps) {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const [showDialog, setShowDialog] = useState(false);
    const filesCount = useAppSelector(selectTotalFiles);

    const handleReindex = () => {
        if (!searchQuery && !file_id) return;
        dispatch(setBackgroundTaskSpinnerActive());
        let result: Promise<void>;
        if (file_id) {
            result = scheduleSingleFileIndexing(file_id);
        } else if (searchQuery) {
            result = scheduleFileIndexing(searchQuery);
        } else {
            toast.error("Error while opening Dialog: No File or Query found");
            return;
        }

        result
            .then(() => {
                toast.success(
                    "Re-indexing successfully scheduled, this might take a while. Refresh the page to see the results.",
                );
                dispatch(updateQuery(searchQuery!));
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
        if ((!searchQuery && !file_id) || filesCount === 0) return;
        if (file_id) {
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
            {file_id || icon_only ? (
                <IconButton
                    onClick={() => startReindexProcess()}
                    disabled={disabled}
                    title="Re-index"
                    aria-label="re-index"
                >
                    <YoutubeSearchedForOutlined />
                </IconButton>
            ) : (
                <Button
                    onClick={() => startReindexProcess()}
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
                        onClick={() => setShowDialog(false)}
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
                        onClick={() => setShowDialog(false)}
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
}
