import { Label } from "@mui/icons-material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { deleteTagFromFiles } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import {
    DialogProps,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";

import { ConfirmDialog } from "..";

interface DeleteTagGloballyDialogProps extends DialogProps {
    tag: string;
}

export const DeleteTagGloballyDialog = ({
    id,
    onClose,
    tag,
}: DeleteTagGloballyDialogProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const handleDeleteTagGlobally = async () => {
        if (!tag) return;

        setIsLoading(true);
        dispatch(startLoadingIndicator());
        try {
            await deleteTagFromFiles(tag);
            toast.success(t("tagsList.scheduledRemoveTagToast"));
            onClose();
        } catch (err) {
            toast.error(
                t("tagsList.scheduledRemoveErrorToast", {
                    err: err instanceof Error ? err.message : "Unknown error",
                }),
            );
        } finally {
            setIsLoading(false);
            dispatch(stopLoadingIndicator());
        }
    };

    return (
        <ConfirmDialog
            id={id}
            text={t("confirmDialog.confirmTagDeletionText", { tag })}
            buttonText={t("confirmDialog.confirmTagDeletion")}
            onConfirm={handleDeleteTagGlobally}
            onClose={onClose}
            icon={<Label />}
            loading={isLoading}
        />
    );
};
