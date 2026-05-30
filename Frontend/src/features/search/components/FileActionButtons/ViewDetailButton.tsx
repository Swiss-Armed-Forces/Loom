import { Preview } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";
import { FileDetailTab } from "@features/common/utils/enums";
import { SearchQuery } from "@features/common/utils/model";

import { FileActionButtonProps } from ".";

interface ViewDetailButtonProps extends FileActionButtonProps {
    fileId: string;
    searchQuery: SearchQuery | null;
}

export const ViewDetailButton = ({
    fileId,
    searchQuery,
    disabled = false,
}: ViewDetailButtonProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const handleViewDetail = useCallback(() => {
        dispatch(
            openDialog({
                id: "",
                type: DialogType.FileDetail,
                props: {
                    fileId,
                    searchQuery,
                    tab: FileDetailTab.Rendered,
                },
            }),
        );
    }, [dispatch, fileId, searchQuery]);

    return (
        <IconButton
            disabled={disabled}
            aria-label="preview"
            title={t("generalSearchView.viewDetails")}
            onClick={handleViewDetail}
        >
            <Preview />
        </IconButton>
    );
};
