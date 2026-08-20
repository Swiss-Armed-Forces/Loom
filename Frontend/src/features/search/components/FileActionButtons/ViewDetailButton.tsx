import { Preview } from "@mui/icons-material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openFileTabThunk } from "@app/slices/searchSlice";
import { SearchQuery } from "@features/common/utils/model";

import { FileActionButtonBase } from "./FileActionButtonBase";

import { FileActionButtonProps } from ".";

interface ViewDetailButtonProps extends FileActionButtonProps {
    fileId: string;
    searchQuery: SearchQuery | null;
}

export const ViewDetailButton = ({
    fileId,
    disabled = false,
    disableTooltip = false,
}: ViewDetailButtonProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const handleViewDetail = useCallback(
        (background = false) => {
            dispatch(openFileTabThunk({ fileId, background }));
        },
        [dispatch, fileId],
    );

    return (
        <FileActionButtonBase
            icon={<Preview />}
            label={t("generalSearchView.viewDetails")}
            onClick={(e) => handleViewDetail(e.ctrlKey)}
            iconOnly
            disabled={disabled}
            disableTooltip={disableTooltip}
            ariaLabel="preview"
        />
    );
};
