import { Close, UploadFile } from "@mui/icons-material";
import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { xhrUpload } from "@app/api/xhrUpload";
import { useAppDispatch } from "@app/hooks";
import {
    DialogProps,
    setBackgroundTaskSpinnerActive,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import { notifyIfUnavailableInDemoMode } from "@features/common/demoModeUnavailableAction";
import { useFileUpload } from "@features/common/hooks/useFileUpload";
import { DemoUnavailableFeature } from "@features/common/utils/demoMode";

import { DialogBase, FileDropzone } from "..";

export const UploadFileDialog = ({ id, onClose, isTop }: DialogProps) => {
    const {
        files,
        setFiles,
        isLoading,
        overallProgress,
        handleUpload,
        abortUpload,
    } = useFileUpload();
    const dispatch = useAppDispatch();
    const { t } = useTranslation();

    const handleClose = () => {
        abortUpload();
        onClose();
    };

    const handleSubmit = async () => {
        if (notifyIfUnavailableInDemoMode(DemoUnavailableFeature.FileUpload))
            return;

        dispatch(startLoadingIndicator());
        try {
            await handleUpload((file, onProgress, signal) =>
                xhrUpload("/v1/files", file, onProgress, signal),
            );
            toast.success("Files successfully uploaded");
            dispatch(setBackgroundTaskSpinnerActive());
            onClose();
        } catch (error) {
            if (!(
                error instanceof DOMException && error.name === "AbortError"
            )) {
                toast.error("Cannot upload files. Reason: " + error);
            }
        }
        dispatch(stopLoadingIndicator());
    };

    return (
        <DialogBase
            id={id}
            onClose={handleClose}
            isTop={isTop}
            title={t("uploadFileDialog.title")}
            loading={isLoading}
            uploadProgress={overallProgress}
            actions={
                <>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        onClick={handleClose}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        startIcon={<UploadFile />}
                        variant="contained"
                        disabled={files.length === 0 || isLoading}
                        onClick={handleSubmit}
                    >
                        {t("uploadFileDialog.uploadButton")}
                    </Button>
                </>
            }
        >
            <FileDropzone
                multiple={true}
                dropzoneText={t("uploadFileDialog.dropzoneText")}
                files={files}
                onFilesChange={setFiles}
                disabled={isLoading}
            />
        </DialogBase>
    );
};
