import { UploadFile } from "@mui/icons-material";
import { Button, IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";

import { FileActionButtonProps } from ".";

type UploadFileButtonProps = Omit<FileActionButtonProps, "filePreview">;

export const UploadFileButton = ({
    iconOnly = false,
}: UploadFileButtonProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();

    const handleClick = () => {
        dispatch(
            openDialog({
                id: "",
                type: DialogType.UploadFile,
            }),
        );
    };

    if (iconOnly) {
        return (
            <IconButton
                onClick={handleClick}
                title={t("uploadFileDialog.uploadButton")}
            >
                <UploadFile />
            </IconButton>
        );
    }

    return (
        <Button
            variant="contained"
            startIcon={<UploadFile />}
            color="secondary"
            onClick={handleClick}
            fullWidth
        >
            {t("uploadFileDialog.uploadButton")}
        </Button>
    );
};
