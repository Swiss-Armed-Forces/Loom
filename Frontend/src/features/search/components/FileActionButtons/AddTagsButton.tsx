import { LabelOutlined } from "@mui/icons-material";
import LabelIcon from "@mui/icons-material/Label";
import { Button, IconButton } from "@mui/material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks.ts";
import { openDialog } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";

import { FileActionButtonProps } from ".";

export const AddTagsButton = ({
    filePreview,
    disabled = false,
    iconOnly = false,
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

    if (iconOnly) {
        return (
            <IconButton
                aria-label="tags-input"
                onClick={handleClick}
                disabled={disabled}
                title={t("tags.addTag")}
            >
                <LabelIcon />
            </IconButton>
        );
    }
    return (
        <Button
            onClick={handleClick}
            disabled={disabled}
            color="secondary"
            variant="contained"
            startIcon={<LabelOutlined />}
            fullWidth
        >
            <span className="btn-label">{t("tags.addTag")}</span>
        </Button>
    );
};
