import { Close, UploadFile } from "@mui/icons-material";
import FileIcon from "@mui/icons-material/Attachment";
import UploadIcon from "@mui/icons-material/CloudUpload";
import { Avatar, Button, Chip } from "@mui/material";
import { useState } from "react";
import Dropzone from "react-dropzone";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { uploadFile } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import {
    DialogProps,
    setBackgroundTaskSpinnerActive,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";

import { DialogBase } from "..";

import styles from "./UploadFileDialog.module.css";

export const UploadFileDialog = ({ id, onClose }: DialogProps) => {
    const [files, setFiles] = useState<File[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const dispatch = useAppDispatch();
    const { t } = useTranslation();

    const addFiles = (filesToUpload: File[]) => {
        setFiles(files.concat(filesToUpload));
    };
    const removeFile = (file: File) => {
        setFiles(files.filter((f) => f !== file));
    };

    const handleUpload = async () => {
        setIsLoading(true);
        dispatch(startLoadingIndicator());
        try {
            await Promise.all(files.map((file) => uploadFile(file)));
            toast.success("Files successfully uploaded");
            dispatch(setBackgroundTaskSpinnerActive());
            onClose();
        } catch (error) {
            toast.error("Cannot upload files. Reason: " + error);
        }
        setIsLoading(false);
        dispatch(stopLoadingIndicator());
    };

    return (
        <DialogBase
            id={id}
            onClose={onClose}
            title={t("uploadFileDialog.title")}
            loading={isLoading}
            actions={
                <>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        onClick={onClose}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        startIcon={<UploadFile />}
                        variant="contained"
                        disabled={files.length === 0 || isLoading}
                        onClick={handleUpload}
                    >
                        {t("uploadFileDialog.uploadButton")}
                    </Button>
                </>
            }
        >
            <Dropzone onDrop={addFiles} multiple={true}>
                {({ getRootProps, getInputProps, isDragActive }) => (
                    <div
                        {...getRootProps()}
                        style={{
                            width: "100%",
                            height: "30vh",
                            borderWidth: "2px",
                            borderColor: isDragActive ? "#31312e" : "#BDBDBD",
                            borderStyle: "dashed",
                            borderRadius: "5px",
                            backgroundColor: "#E0E0E0",
                            cursor: "pointer",
                            boxSizing: "border-box",
                        }}
                    >
                        <div className={styles.uploadFileDropzone} style={{}}>
                            <div className={styles.uploadFileDropzoneText}>
                                {t("uploadFileDialog.dropzoneText")}
                            </div>
                            <UploadIcon
                                className={styles.uploadFileDropzoneIcon}
                            />
                            <input {...getInputProps()} />
                        </div>
                    </div>
                )}
            </Dropzone>
            {files.length > 0 && (
                <div className={styles.fileList}>
                    {files.map((file, idx) => (
                        <Chip
                            key={idx}
                            label={file.name}
                            variant="outlined"
                            avatar={
                                <Avatar>
                                    <FileIcon />
                                </Avatar>
                            }
                            onDelete={() => {
                                removeFile(file);
                            }}
                        />
                    ))}
                </div>
            )}
        </DialogBase>
    );
};
