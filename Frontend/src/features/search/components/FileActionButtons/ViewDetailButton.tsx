import { Preview } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openFileTabThunk } from "@app/slices/searchSlice";
import { SearchQuery } from "@features/common/utils/model";

import { FileActionButtonProps } from ".";

interface ViewDetailButtonProps extends FileActionButtonProps {
    fileId: string;
    searchQuery: SearchQuery | null;
}

export const ViewDetailButton = ({
    fileId,
    disabled = false,
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
        <IconButton
            disabled={disabled}
            aria-label="preview"
            title={t("generalSearchView.viewDetails")}
            onClick={(e) => handleViewDetail(e.ctrlKey)}
        >
            <Preview />
        </IconButton>
    );
};
