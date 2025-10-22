import { useState } from "react";
import { SummarizeOutlined } from "@mui/icons-material";
import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    TextField,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { Close } from "@mui/icons-material";
import {
    scheduleFileSummarization,
    scheduleSingleFileSummarization,
} from "../../../app/api";
import { setBackgroundTaskSpinnerActive } from "../../common/commonSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { toast } from "react-toastify";
import {
    selectQuery,
    selectSummarizationSystemPrompt,
    selectTotalFiles,
} from "../searchSlice";

interface SummarizeProps {
    file_id?: string;
    system_prompt?: string;
    disabled?: boolean;
    icon_only?: boolean;
}

export function SummaryButton({
    file_id,
    disabled = false,
    icon_only = false,
}: SummarizeProps) {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const summarizationSystemPrompt = useAppSelector(
        selectSummarizationSystemPrompt,
    );
    const [showDialog, setShowDialog] = useState(false);
    const [systemPrompt, setSystemPrompt] = useState<string | null>(null);
    const filesCount = useAppSelector(selectTotalFiles);

    const handleSummarize = () => {
        if (!searchQuery) return;
        if (!file_id) return;
        dispatch(setBackgroundTaskSpinnerActive());
        let result: Promise<void>;
        if (file_id) {
            result = scheduleSingleFileSummarization(file_id, systemPrompt);
        } else if (searchQuery) {
            result = scheduleFileSummarization(searchQuery, systemPrompt);
        } else {
            toast.error("Error while opening Dialog: No File or Query found");
            return;
        }

        result
            .then(() => {
                toast.success(
                    "Summary successfully scheduled, this might take a while.",
                );
            })
            .catch((err) => {
                toast.error(
                    "Cannot summarize files. Code: " +
                        err.status +
                        ", Text: " +
                        err.text,
                );
            });
        setShowDialog(false);
    };

    const startSummaryProcess = () => {
        if ((!searchQuery && !file_id) || filesCount === 0) return;
        setShowDialog(true);
    };

    const handleCloseDialog = (_: unknown, reason: string) => {
        if (reason && reason == "backdropClick") {
            return;
        }
        setShowDialog(false);
    };

    return (
        <>
            {file_id || icon_only ? (
                <IconButton
                    onClick={() => startSummaryProcess()}
                    disabled={disabled}
                    title="Summarize"
                    aria-label="summarize"
                >
                    <SummarizeOutlined />
                </IconButton>
            ) : (
                <Button
                    onClick={() => startSummaryProcess()}
                    disabled={disabled}
                    color="secondary"
                    fullWidth={true}
                    variant={"contained"}
                    startIcon={<SummarizeOutlined />}
                >
                    <span className="btn-label">
                        {t("summarizationDialog.executeButton")}
                    </span>
                </Button>
            )}
            <Dialog
                open={showDialog}
                fullWidth={true}
                onClose={handleCloseDialog}
            >
                <DialogTitle>
                    {t("summarizationDialog.title")}
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
                    <p>{t("summarizationDialog.systemPromptHint")}</p>
                    <TextField
                        fullWidth
                        variant="outlined"
                        multiline={true}
                        value={systemPrompt ?? ""}
                        placeholder={summarizationSystemPrompt ?? ""}
                        label="System Prompt"
                        minRows={2}
                        maxRows={4}
                        onChange={(e) =>
                            setSystemPrompt(e.target.value || null)
                        }
                    />
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
                        startIcon={<SummarizeOutlined />}
                        onClick={handleSummarize}
                        color="primary"
                        variant="contained"
                    >
                        {t("sideMenu.summarizeQueriedFiles")}
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
}
