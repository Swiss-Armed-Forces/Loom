import { Delete } from "@mui/icons-material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { deleteArchive } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { removeArchive } from "@app/slices/archiveSlice";
import { DialogProps } from "@app/slices/commonSlice";

import { ConfirmDialog } from "..";

interface DeleteArchiveDialogProps extends DialogProps {
    archiveId: string;
}

export const DeleteArchiveDialog = ({
    id,
    onClose,
    isTop,
    archiveId,
}: DeleteArchiveDialogProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const handleConfirmation = async () => {
        setIsLoading(true);
        await deleteArchive(archiveId);
        dispatch(removeArchive(archiveId));
        onClose();
        setIsLoading(false);
    };

    return (
        <ConfirmDialog
            id={id}
            isTop={isTop}
            text={t("confirmDialog.confirmArchiveDeletion")}
            buttonText={t("confirmDialog.confirmRemoval")}
            onConfirm={handleConfirmation}
            onClose={onClose}
            icon={<Delete />}
            loading={isLoading}
        />
    );
};
