import { ArchiveOutlined } from "@mui/icons-material";
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

import { ConfirmDialog } from "..";

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

    const startArchiveCreation = async () => {
        if (!searchQuery) return;
        setIsLoading(true);
        dispatch(startLoadingIndicator());
        try {
            await scheduleArchiveCreation(searchQuery);
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
            isTop={isTop}
            text={t("confirmDialog.confirmArchiveCreationText")}
            buttonText={t("confirmDialog.confirmArchiveCreation")}
            onConfirm={startArchiveCreation}
            onClose={onClose}
            icon={<ArchiveOutlined />}
            loading={isLoading}
        />
    );
};
