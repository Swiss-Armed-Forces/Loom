import { LabelOutlined } from "@mui/icons-material";
import { Button, IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useAppDispatch } from "../../../../app/hooks.ts";

import {
    ActionType,
    setAction,
    setFileDetailData,
} from "../../../search/searchSlice.ts";
import LabelIcon from "@mui/icons-material/Label";
import { GetFilePreviewResponse } from "../../../../app/api";
import { useCallback } from "react";
interface TagsInputProps {
    filePreview?: GetFilePreviewResponse;
    button_full_width?: boolean;
    disabled?: boolean;
    icon_only?: boolean;
}

export function TagsInput({
    filePreview,
    button_full_width = false,
    disabled = false,
    icon_only = false,
}: TagsInputProps) {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const handleClick = useCallback(() => {
        dispatch(
            setFileDetailData({
                filePreview: filePreview,
            }),
        );
        dispatch(setAction(ActionType.TAGS));
    }, [dispatch, filePreview]);

    if (icon_only) {
        return (
            <IconButton
                aria-label="tags-input"
                onClick={handleClick}
                disabled={disabled}
                title={t("tags.addTag")}
            >
                <LabelIcon></LabelIcon>
            </IconButton>
        );
    }
    return (
        <Button
            onClick={handleClick}
            disabled={disabled}
            color="secondary"
            variant={button_full_width ? "contained" : "text"}
            startIcon={button_full_width ? <LabelOutlined /> : null}
            fullWidth={button_full_width}
        >
            <span className="btn-label">{t("tags.addTag")}</span>
        </Button>
    );
}
