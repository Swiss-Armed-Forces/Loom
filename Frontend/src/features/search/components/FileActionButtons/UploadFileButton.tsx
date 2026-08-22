import { UploadFile } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";

import { FileActionButtonBase } from "./FileActionButtonBase";

import { FileActionButtonProps } from ".";

type UploadFileButtonProps = Omit<FileActionButtonProps, "filePreview">;

export const UploadFileButton = ({
    iconOnly = false,
    disableTooltip = false,
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

    return (
        <FileActionButtonBase
            icon={<UploadFile />}
            label={t("uploadFileDialog.uploadButton")}
            onClick={handleClick}
            iconOnly={iconOnly}
            disableTooltip={disableTooltip}
            iconButtonSx={{
                bgcolor: "primary.main",
                color: "primary.contrastText",
                "&:hover": { bgcolor: "primary.dark" },
            }}
        />
    );
};
