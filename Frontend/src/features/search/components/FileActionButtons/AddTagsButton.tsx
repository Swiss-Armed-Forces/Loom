import { LabelOutlined } from "@mui/icons-material";
import LabelIcon from "@mui/icons-material/Label";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks.ts";
import { openDialog } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";

import { FileActionButtonBase } from "./FileActionButtonBase";

import { FileActionButtonProps } from ".";

export const AddTagsButton = ({
    filePreview,
    disabled = false,
    iconOnly = false,
    disableTooltip = false,
}: FileActionButtonProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const handleClick = useCallback(() => {
        dispatch(
            openDialog({
                id: "",
                type: DialogType.AddTagsDialog,
                props: { filePreview },
            }),
        );
    }, [dispatch, filePreview]);

    return (
        <FileActionButtonBase
            icon={<LabelIcon />}
            buttonIcon={<LabelOutlined />}
            label={t("tags.addTag")}
            onClick={handleClick}
            iconOnly={iconOnly}
            disabled={disabled}
            disableTooltip={disableTooltip}
            ariaLabel="tags-input"
        />
    );
};
