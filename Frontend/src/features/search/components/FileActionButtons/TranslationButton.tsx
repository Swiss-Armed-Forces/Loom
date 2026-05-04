import { Translate } from "@mui/icons-material";
import { Button, IconButton } from "@mui/material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse } from "@app/api";
import { useAppSelector, useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { selectQuery } from "@app/slices/searchSlice";
import { DialogType } from "@features/common/utils/enums";

interface TranslationProps {
    filePreview?: GetFilePreviewResponse;
    disabled?: boolean;
    iconOnly?: boolean;
}

export const TranslationButton = ({
    filePreview,
    disabled = false,
    iconOnly = false,
}: TranslationProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);

    const handleClick = useCallback(() => {
        dispatch(
            openDialog({
                id: "",
                type: DialogType.Translation,
                props: { fileId: filePreview?.fileId, searchQuery },
            }),
        );
    }, [dispatch, filePreview, searchQuery]);

    if (iconOnly) {
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
};
