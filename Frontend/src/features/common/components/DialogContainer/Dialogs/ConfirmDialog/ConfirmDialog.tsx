import { Close } from "@mui/icons-material";
import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";

import { DialogProps } from "@app/slices/commonSlice";

import { DialogBase } from "../DialogBase";

interface ConfirmDialogProps extends DialogProps {
    text: string;
    buttonText: string;
    onConfirm: () => void;
    icon: React.ReactNode;
    loading: boolean;
    children?: React.ReactNode;
}

export const ConfirmDialog = ({
    id,
    onClose,
    isTop,
    text,
    buttonText,
    onConfirm,
    icon,
    loading,
    children,
}: ConfirmDialogProps) => {
    const { t } = useTranslation();

    return (
        <DialogBase
            id={id}
            onClose={onClose}
            isTop={isTop}
            title={t("confirmDialog.title")}
            loading={loading}
            actions={
                <>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        onClick={onClose}
                        disabled={loading}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        startIcon={icon}
                        variant="contained"
                        onClick={onConfirm}
                        disabled={loading}
                    >
                        {buttonText}
                    </Button>
                </>
            }
        >
            <div>{text}</div>
            {children}
        </DialogBase>
    );
};
