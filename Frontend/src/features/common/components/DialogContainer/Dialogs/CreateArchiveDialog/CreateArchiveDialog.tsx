import { ArchiveOutlined } from "@mui/icons-material";
import { TextField } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { scheduleArchiveCreation } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import {
    DialogProps,
    setBackgroundTaskSpinnerActive,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import { SearchQuery } from "@features/common/utils/model";

import { ConfirmDialog } from "../ConfirmDialog/ConfirmDialog";

interface CreateArchiveDialogProps extends DialogProps {
    searchQuery: SearchQuery;
}

export const CreateArchiveDialog = ({
    id,
    onClose,
    isTop,
    searchQuery,
}: CreateArchiveDialogProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [note, setNote] = useState<string>("");

    const startArchiveCreation = async () => {
        if (!searchQuery) return;
        setIsLoading(true);
        dispatch(startLoadingIndicator());
        try {
            await scheduleArchiveCreation(
                { ...searchQuery, id: null },
                note || undefined,
            );
            dispatch(setBackgroundTaskSpinnerActive());
            toast.success(
                "Creation of archive successfully scheduled. Please go to archives.",
            );
            onClose();
        } catch (error: any) {
            toast.error(
                "Cannot schedule archive creation. Code: " +
                    error.status +
                    ", Text: " +
                    error.text,
            );
        } finally {
            dispatch(stopLoadingIndicator());
            setIsLoading(false);
        }
    };
    return (
        <ConfirmDialog
            id={id}
            onClose={onClose}
            isTop={isTop}
            text={t("confirmDialog.confirmArchiveCreationText")}
            buttonText={t("confirmDialog.confirmArchiveCreation")}
            onConfirm={startArchiveCreation}
            icon={<ArchiveOutlined />}
            loading={isLoading}
        >
            <TextField
                fullWidth
                variant="outlined"
                label={t("archives.noteLabel")}
                multiline={true}
                minRows={2}
                maxRows={4}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                disabled={isLoading}
                sx={{ mt: 2 }}
                slotProps={{
                    htmlInput: {
                        maxLength: 1000,
                    },
                }}
            />
        </ConfirmDialog>
    );
};
