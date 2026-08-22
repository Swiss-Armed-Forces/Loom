import { ImageSearch } from "@mui/icons-material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { selectQuery, selectTotalFiles } from "@app/slices/searchSlice";
import { DialogType } from "@features/common/utils/enums";

import { FileActionButtonBase } from "./FileActionButtonBase";

interface ImageDescriptionProps {
    filePreview?: GetFilePreviewResponse;
    disabled?: boolean;
    iconOnly?: boolean;
    disableTooltip?: boolean;
}

export const ImageDescriptionButton = ({
    filePreview,
    disabled = false,
    iconOnly = false,
    disableTooltip = false,
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

    return (
        <FileActionButtonBase
            icon={<ImageSearch />}
            label={t("imageDescriptionButton.describeImage")}
            onClick={handleClick}
            iconOnly={!!filePreview?.fileId || iconOnly}
            disabled={disabled}
            disableTooltip={disableTooltip}
            ariaLabel="describe-image"
        />
    );
};
