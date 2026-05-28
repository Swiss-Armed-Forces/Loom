import { ImageSearch } from "@mui/icons-material";
import { Button, IconButton } from "@mui/material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { selectQuery, selectTotalFiles } from "@app/slices/searchSlice";
import { DialogType } from "@features/common/utils/enums";

interface ImageDescriptionProps {
    filePreview?: GetFilePreviewResponse;
    disabled?: boolean;
    iconOnly?: boolean;
}

export const ImageDescriptionButton = ({
    filePreview,
    disabled = false,
    iconOnly = false,
}: ImageDescriptionProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const filesCount = useAppSelector(selectTotalFiles);

    const handleClick = useCallback(() => {
        if ((!searchQuery && !filePreview?.fileId) || filesCount === 0) return;
        dispatch(
            openDialog({
                id: "",
                type: DialogType.ImageDescription,
                props: {
                    fileId: filePreview?.fileId,
                    searchQuery: searchQuery,
                },
            }),
        );
    }, [dispatch, filesCount, filePreview, searchQuery]);

    if (filePreview?.fileId || iconOnly) {
        return (
            <IconButton
                onClick={handleClick}
                disabled={disabled}
                title={t("imageDescriptionButton.describeImage")}
                aria-label="describe-image"
            >
                <ImageSearch />
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
            startIcon={<ImageSearch />}
        >
            <span className="btn-label">
                {t("imageDescriptionButton.describeImage")}
            </span>
        </Button>
    );
};
