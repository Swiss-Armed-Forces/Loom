import { Translate } from "@mui/icons-material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse } from "@app/api";
import { useAppSelector, useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { selectQuery } from "@app/slices/searchSlice";
import { DialogType } from "@features/common/utils/enums";

import { FileActionButtonBase } from "./FileActionButtonBase";

interface TranslationProps {
    filePreview?: GetFilePreviewResponse;
    disabled?: boolean;
    iconOnly?: boolean;
    disableTooltip?: boolean;
}

export const TranslationButton = ({
    filePreview,
    disabled = false,
    iconOnly = false,
    disableTooltip = false,
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

    return (
        <FileActionButtonBase
            icon={<Translate />}
            label={t("sideMenu.translateQueriedFiles")}
            onClick={handleClick}
            iconOnly={iconOnly}
            disabled={disabled}
            disableTooltip={disableTooltip}
            ariaLabel="translate"
        />
    );
};
