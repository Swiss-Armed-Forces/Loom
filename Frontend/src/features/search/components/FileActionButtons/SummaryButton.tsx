import { SummarizeOutlined } from "@mui/icons-material";
import { Button, IconButton } from "@mui/material";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { selectQuery, selectTotalFiles } from "@app/slices/searchSlice";
import { DialogType } from "@features/common/utils/enums";

import { GetFilePreviewResponse } from "../../../../app/api";

interface SummarizeProps {
    filePreview?: GetFilePreviewResponse;
    system_prompt?: string;
    disabled?: boolean;
    iconOnly?: boolean;
}

export const SummaryButton = ({
    filePreview,
    disabled = false,
    iconOnly = false,
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
                    fileId: filePreview.fileId,
                    searchQuery: searchQuery,
                },
            }),
        );
    }, [dispatch, filesCount, filePreview, searchQuery]);

    if (iconOnly) {
        return (
            <IconButton
                onClick={handleClick}
                disabled={disabled}
                title="Summarize"
                aria-label="summarize"
            >
                <SummarizeOutlined />
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
            startIcon={<SummarizeOutlined />}
        >
            <span className="btn-label">
                {t("summarizationDialog.executeButton")}
            </span>
        </Button>
    );
};
