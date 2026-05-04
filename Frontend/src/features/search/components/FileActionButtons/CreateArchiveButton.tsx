import { ArchiveOutlined } from "@mui/icons-material";
import { Button, IconButton } from "@mui/material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";
import { SearchQuery } from "@features/common/utils/model";

import { FileActionButtonProps } from ".";

interface CreateArchiveButtonProps extends Omit<
    FileActionButtonProps,
    "filePreview"
> {
    searchQuery: SearchQuery;
}

export const CreateArchiveButton = ({
    searchQuery,
    disabled = false,
    iconOnly = false,
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

    if (iconOnly) {
        return (
            <IconButton
                onClick={handleClick}
                disabled={disabled}
                title={t("sideMenu.createArchive")}
            >
                <ArchiveOutlined />
            </IconButton>
        );
    }
    return (
        <Button
            onClick={handleClick}
            disabled={disabled}
            color="secondary"
            variant="contained"
            startIcon={<ArchiveOutlined />}
            fullWidth={true}
        >
            <span className="btn-label">{t("sideMenu.createArchive")}</span>
        </Button>
    );
};
