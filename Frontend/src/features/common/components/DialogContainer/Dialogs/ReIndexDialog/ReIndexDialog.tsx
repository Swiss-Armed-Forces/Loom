import { Close, YoutubeSearchedForOutlined } from "@mui/icons-material";
import { Box, Button, Slider, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
    ResponseError,
    scheduleFileIndexing,
    scheduleSingleFileIndexing,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    DialogProps,
    setBackgroundTaskSpinnerActive,
} from "@app/slices/commonSlice";
import {
    selectIndexingAdditionalRecursionDepth,
    selectTotalFiles,
    setIndexingAdditionalRecursionDepth,
} from "@app/slices/searchSlice";
import { SearchQuery } from "@features/common/utils/model";

import { DialogBase } from "../DialogBase";

// The API caps the depth at 20; the slider stops well short of that because every
// level multiplies the number of extracted files.
const MAX_SELECTABLE_RECURSION_DEPTH = 7;

interface ReIndexDialogProps extends DialogProps {
    fileId?: string;
    searchQuery: SearchQuery;
}

export const ReIndexDialog = ({
    id,
    onClose,
    isTop,
    fileId,
    searchQuery,
}: ReIndexDialogProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const filesCount = useAppSelector(selectTotalFiles);
    const additionalRecursionDepth = useAppSelector(
        selectIndexingAdditionalRecursionDepth,
    );
    const [isLoading, setIsLoading] = useState(false);

    const getErrorMessage = async (error: unknown): Promise<string> => {
        if (error instanceof ResponseError) {
            try {
                const errorData = await error.response.json();
                return errorData?.detail ?? JSON.stringify(errorData);
            } catch {
                return error.message || "Unknown error";
            }
        }

        if (error instanceof Error) {
            return error.message;
        }

        return String(error);
    };

    const handleReindex = async () => {
        if (!searchQuery && !fileId) return;

        dispatch(setBackgroundTaskSpinnerActive());
        setIsLoading(true);
        try {
            if (fileId) {
                await scheduleSingleFileIndexing(
                    fileId,
                    additionalRecursionDepth,
                );
            } else {
                await scheduleFileIndexing(
                    { ...searchQuery, id: null },
                    additionalRecursionDepth,
                );
            }

            toast.success(t("reIndex.scheduledToast"));
            onClose();
        } catch (error) {
            toast.error(
                t("reIndex.scheduledErrorToast", {
                    err: await getErrorMessage(error),
                }),
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <DialogBase
            id={id}
            onClose={onClose}
            isTop={isTop}
            title={t("reIndex.confirmationTitle")}
            loading={isLoading}
            actions={
                <>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        tabIndex={2}
                        onClick={onClose}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        startIcon={<YoutubeSearchedForOutlined />}
                        onClick={handleReindex}
                        color="primary"
                        variant="contained"
                        tabIndex={1}
                    >
                        {t("reIndex.executeButton")}
                    </Button>
                </>
            }
        >
            <p>
                {t("reIndex.confirmationMessage", {
                    count: fileId !== undefined ? 1 : filesCount,
                })}
            </p>
            <Box sx={{ display: "grid", gap: 0.25 }}>
                <Box
                    sx={{
                        display: "flex",
                        alignItems: "baseline",
                        gap: 1,
                    }}
                >
                    <Typography variant="subtitle2" sx={{ flex: 1 }}>
                        {t("reIndex.additionalRecDepthLabel")}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                        {additionalRecursionDepth}
                    </Typography>
                </Box>
                <Slider
                    size="small"
                    min={0}
                    max={MAX_SELECTABLE_RECURSION_DEPTH}
                    step={1}
                    marks
                    value={additionalRecursionDepth}
                    valueLabelDisplay="auto"
                    onChange={(_, next) => {
                        const picked = Array.isArray(next) ? next[0] : next;
                        dispatch(setIndexingAdditionalRecursionDepth(picked));
                    }}
                />
                <Typography variant="caption" color="text.secondary">
                    {t("reIndex.additionalRecDepthHint")}
                </Typography>
            </Box>
        </DialogBase>
    );
};
