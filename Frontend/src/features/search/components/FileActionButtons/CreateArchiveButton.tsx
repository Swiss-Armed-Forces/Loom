import { ArchiveOutlined } from "@mui/icons-material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";
import { SearchQuery } from "@features/common/utils/model";

import { FileActionButtonBase } from "./FileActionButtonBase";

import { FileActionButtonProps } from ".";

interface CreateArchiveButtonProps extends Omit<
    FileActionButtonProps,
    "filePreview"
> {
    searchQuery: SearchQuery | null;
}

export const CreateArchiveButton = ({
    searchQuery,
    disabled = false,
    iconOnly = false,
    disableTooltip = false,
}: CreateArchiveButtonProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const handleClick = useCallback(() => {
        dispatch(
            openDialog({
                id: "",
                type: DialogType.CreateArchive,
                props: { searchQuery },
            }),
        );
    }, [dispatch, searchQuery]);

    return (
        <FileActionButtonBase
            icon={<ArchiveOutlined />}
            label={t("sideMenu.createArchive")}
            onClick={handleClick}
            iconOnly={iconOnly}
            disabled={disabled}
            disableTooltip={disableTooltip}
            dataTour="create-archive-button"
        />
    );
};
