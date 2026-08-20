import { SummarizeOutlined } from "@mui/icons-material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { selectQuery, selectTotalFiles } from "@app/slices/searchSlice";
import { DialogType } from "@features/common/utils/enums";

import { GetFilePreviewResponse } from "../../../../app/api";

import { FileActionButtonBase } from "./FileActionButtonBase";

interface SummarizeProps {
    filePreview?: GetFilePreviewResponse;
    system_prompt?: string;
    disabled?: boolean;
    iconOnly?: boolean;
    disableTooltip?: boolean;
}

export const SummaryButton = ({
    filePreview,
    disabled = false,
    iconOnly = false,
    disableTooltip = false,
}: SummarizeProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const filesCount = useAppSelector(selectTotalFiles);

    const handleClick = useCallback(() => {
        if ((!searchQuery && !filePreview?.fileId) || filesCount === 0) return;
        dispatch(
            openDialog({
                id: "",
                type: DialogType.Summary,
                props: {
                    fileId: filePreview?.fileId,
                    searchQuery: searchQuery,
                },
            }),
        );
    }, [dispatch, filesCount, filePreview, searchQuery]);

    return (
        <FileActionButtonBase
            icon={<SummarizeOutlined />}
            label={t("summarizationDialog.executeButton")}
            onClick={handleClick}
            iconOnly={iconOnly}
            disabled={disabled}
            disableTooltip={disableTooltip}
            ariaLabel="summarize"
        />
    );
};
