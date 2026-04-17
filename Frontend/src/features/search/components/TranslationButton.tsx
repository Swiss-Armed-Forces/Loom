import { Translate } from "@mui/icons-material";
import { Button, IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useAppSelector, useAppDispatch } from "../../../app/hooks";
import { GetFilePreviewResponse } from "../../../app/api";
import {
    ActionType,
    setAction,
    selectQuery,
    setFileDetailData,
} from "../searchSlice";
import { useCallback } from "react";

interface TranslationProps {
    filePreview?: GetFilePreviewResponse;
    disabled?: boolean;
    icon_only?: boolean;
}

export function TranslationButton({
    filePreview,
    disabled = false,
    icon_only = false,
}: TranslationProps) {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);

    const handleClick = useCallback(() => {
        dispatch(
            setFileDetailData({
                filePreview: filePreview,
                searchQuery: searchQuery,
            }),
        );
        dispatch(setAction(ActionType.TRANSLATE));
    }, [dispatch, filePreview, searchQuery]);

    if (filePreview?.fileId || icon_only) {
        return (
            <IconButton
                onClick={handleClick}
                disabled={disabled}
                title="Translate"
                aria-label="translate"
            >
                <Translate />
            </IconButton>
        );
    }
    return (
        <Button
            onClick={handleClick}
            disabled={disabled}
            color="secondary"
            fullWidth={true}
            variant={"contained"}
            startIcon={<Translate />}
        >
            <span className="btn-label">
                {t("sideMenu.translateQueriedFiles")}
            </span>
        </Button>
    );
}
