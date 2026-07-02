import { Delete } from "@mui/icons-material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { DialogProps } from "@app/slices/commonSlice";
import { CustomQuery, deleteCustomQuery } from "@app/slices/searchSlice";

import { ConfirmDialog } from "..";

interface DeleteCustomQueryDialogProps extends DialogProps {
    customQuery: CustomQuery;
}

export const DeleteCustomQueryDialog = ({
    id,
    onClose,
    isTop,
    customQuery,
}: DeleteCustomQueryDialogProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const handleConfirmation = async () => {
        setIsLoading(true);
        await dispatch(deleteCustomQuery(customQuery));
        onClose();
        setIsLoading(false);
    };

    return (
        <ConfirmDialog
            id={id}
            isTop={isTop}
            text={t("confirmDialog.confirmCustomQueryRemoval")}
            buttonText={t("confirmDialog.confirmRemoval")}
            onConfirm={handleConfirmation}
            onClose={onClose}
            icon={<Delete />}
            loading={isLoading}
        />
    );
};
