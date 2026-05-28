import { Close, ImageSearch } from "@mui/icons-material";
import { Button, TextField } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
    ResponseError,
    scheduleImageDescriptionByQuery,
    scheduleSingleImageDescription,
} from "@app/api";
import { useAppDispatch } from "@app/hooks";
import {
    DialogProps,
    setBackgroundTaskSpinnerActive,
} from "@app/slices/commonSlice";
import { SearchQuery } from "@features/common/utils/model";

import { DialogBase } from "../DialogBase";

interface ImageDescriptionDialogProps extends DialogProps {
    fileId?: string;
    searchQuery: SearchQuery;
}

export const ImageDescriptionDialog = ({
    id,
    onClose,
    fileId,
    searchQuery,
}: ImageDescriptionDialogProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const [systemPrompt, setSystemPrompt] = useState<string>("");
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

    const startDescribing = async () => {
        if (!searchQuery && !fileId) return;
        dispatch(setBackgroundTaskSpinnerActive());
        setIsLoading(true);
        try {
            if (fileId) {
                await scheduleSingleImageDescription(fileId, systemPrompt);
            } else if (searchQuery) {
                await scheduleImageDescriptionByQuery(
                    searchQuery,
                    systemPrompt,
                );
            }

            toast.success(t("imageDescriptionDialog.scheduledToast"));
            onClose();
        } catch (error: any) {
            toast.error(
                t("imageDescriptionDialog.scheduledErrorToast", {
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
            title={t("imageDescriptionDialog.title")}
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
                        startIcon={<ImageSearch />}
                        onClick={startDescribing}
                        color="primary"
                        variant="contained"
                        tabIndex={1}
                    >
                        {t("imageDescriptionDialog.executeButton")}
                    </Button>
                </>
            }
        >
            <p>{t("imageDescriptionDialog.systemPromptHint")}</p>
            <TextField
                fullWidth
                variant="outlined"
                autoFocus
                multiline={true}
                value={systemPrompt}
                label="System Prompt"
                minRows={2}
                maxRows={4}
                onChange={(e) => setSystemPrompt(e.target.value)}
            />
        </DialogBase>
    );
};
