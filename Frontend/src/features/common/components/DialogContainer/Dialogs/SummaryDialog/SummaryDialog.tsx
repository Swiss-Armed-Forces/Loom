import { SummarizeOutlined } from "@mui/icons-material";
import { Close } from "@mui/icons-material";
import { Button, TextField } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
    ResponseError,
    scheduleFileSummarization,
    scheduleSingleFileSummarization,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    DialogProps,
    setBackgroundTaskSpinnerActive,
} from "@app/slices/commonSlice";
import { selectSummarizationSystemPrompt } from "@app/slices/searchSlice";
import { SearchQuery } from "@features/common/utils/model";

import { DialogBase } from "../DialogBase";

interface SummaryDialogProps extends DialogProps {
    fileId?: string;
    searchQuery: SearchQuery;
}

export const SummaryDialog = ({
    id,
    onClose,
    fileId,
    searchQuery,
}: SummaryDialogProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const summarizationSystemPrompt = useAppSelector(
        selectSummarizationSystemPrompt,
    );
    const [systemPrompt, setSystemPrompt] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

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
        dispatch(setBackgroundTaskSpinnerActive());
        setIsLoading(true);
        try {
            if (fileId) {
                await scheduleSingleFileSummarization(fileId, systemPrompt);
            } else if (searchQuery) {
                await scheduleFileSummarization(searchQuery, systemPrompt);
            }

            toast.success(t("summarizationDialog.scheduledToast"));
            onClose();
        } catch (error: any) {
            toast.error(
                t("summarizationDialog.scheduledErrorToast", {
                    err: await getErrorMessage(error),
                }),
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <DialogBase
            id={id}
            onClose={onClose}
            title={t("summarizationDialog.title")}
            loading={isLoading}
            actions={
                <>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        tabIndex={2}
                        onClick={onClose}
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
                </>
            }
        >
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
        </DialogBase>
    );
};
