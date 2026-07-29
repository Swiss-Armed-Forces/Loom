import { Close } from "@mui/icons-material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { xhrUpload } from "@app/api/xhrUpload";
import { useAppDispatch } from "@app/hooks";
import {
    DialogProps,
    setBackgroundTaskSpinnerActive,
} from "@app/slices/commonSlice";
import { notifyIfUnavailableInDemoMode } from "@features/common/demoModeUnavailableAction";
import { useFileUpload } from "@features/common/hooks/useFileUpload";
import { DemoUnavailableFeature } from "@features/common/utils/demoMode";

import { DialogBase, FileDropzone } from "..";

export const ImportArchiveDialog = ({ id, onClose, isTop }: DialogProps) => {
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
        if (notifyIfUnavailableInDemoMode(DemoUnavailableFeature.ArchiveImport))
            return;

        try {
            await handleUpload((file, onProgress, signal) =>
                xhrUpload("/v1/archive/import", file, onProgress, signal),
            );
            toast.success(t("archives.importSuccess"));
            dispatch(setBackgroundTaskSpinnerActive());
            onClose();
        } catch (error) {
            if (
                !(error instanceof DOMException && error.name === "AbortError")
            ) {
                toast.error(t("archives.importError") + error);
            }
        }
    };

    return (
        <DialogBase
            id={id}
            onClose={handleClose}
            isTop={isTop}
            title={t("archives.importButton")}
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
                        startIcon={<CloudUploadIcon />}
                        variant="contained"
                        disabled={files.length === 0 || isLoading}
                        onClick={handleSubmit}
                    >
                        {t("archives.importButton")}
                    </Button>
                </>
            }
        >
            <FileDropzone
                multiple={false}
                accept={{ "application/zip": [".zip", ".loom"] }}
                dropzoneText={t("archives.importDropzoneText")}
                files={files}
                onFilesChange={setFiles}
                disabled={isLoading}
            />
        </DialogBase>
    );
};
