import { useCallback, useState } from "react";
import { SummarizeOutlined } from "@mui/icons-material";
import {
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
import { Close } from "@mui/icons-material";
import {
    ResponseError,
    scheduleFileSummarization,
    scheduleSingleFileSummarization,
} from "../../../app/api";
import { setBackgroundTaskSpinnerActive } from "../../common/commonSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { toast } from "react-toastify";
import {
    ActionType,
    selectAction,
    setAction,
    selectFileDetailData,
    selectQuery,
    selectSummarizationSystemPrompt,
} from "../searchSlice";

export function SummaryDialog() {
    const fileDetailData = useAppSelector(selectFileDetailData);
    const action = useAppSelector(selectAction);
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const summarizationSystemPrompt = useAppSelector(
        selectSummarizationSystemPrompt,
    );
    const [systemPrompt, setSystemPrompt] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const fileId = fileDetailData.filePreview?.fileId;

    const getErrorMessage = async (error: unknown): Promise<string> => {
        if (error instanceof ResponseError) {
            try {
                const errorData = await error.response.json();
                return errorData?.detail ?? JSON.stringify(errorData);
            } catch {
                return error.message || "Unknown error";
            }
        }

        if (error instanceof Error) {
            return error.message;
        }

        return String(error);
    };

    const startSummarizing = async () => {
        if (!searchQuery && !fileId) return;
        try {
            dispatch(setBackgroundTaskSpinnerActive());
            setIsLoading(true);
            if (fileId) {
                await scheduleSingleFileSummarization(fileId, systemPrompt);
            } else if (searchQuery) {
                await scheduleFileSummarization(searchQuery, systemPrompt);
            }

            toast.success(t("summarizationDialog.scheduledToast"));
        } catch (error: any) {
            toast.error(
                t("summarizationDialog.scheduledErrorToast", {
                    err: await getErrorMessage(error),
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
    if (action != ActionType.SUMMARIZE) return;

    return (
        <Dialog open fullWidth={true} onClose={handleClose}>
            <DialogTitle>
                {t("summarizationDialog.title")}
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
                <p>{t("summarizationDialog.systemPromptHint")}</p>
                <TextField
                    fullWidth
                    variant="outlined"
                    autoFocus
                    multiline={true}
                    value={systemPrompt ?? ""}
                    placeholder={summarizationSystemPrompt ?? ""}
                    label="System Prompt"
                    minRows={2}
                    maxRows={4}
                    onChange={(e) => setSystemPrompt(e.target.value || null)}
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
                    startIcon={<SummarizeOutlined />}
                    onClick={startSummarizing}
                    color="primary"
                    variant="contained"
                    tabIndex={1}
                >
                    {t("sideMenu.summarizeQueriedFiles")}
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
