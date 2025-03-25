import FileIcon from "@mui/icons-material/Attachment";
import UploadIcon from "@mui/icons-material/CloudUpload";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Avatar from "@mui/material/Avatar";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Dropzone from "react-dropzone";
import styles from "./UploadFileDialog.module.css";
import { useState } from "react";
import { Close, UploadFile } from "@mui/icons-material";
import { useAppDispatch } from "../../../app/hooks";
import {
    setBackgroundTaskSpinnerActive,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "../../common/commonSlice";
import { uploadFile } from "../../../app/api";
import { toast } from "react-toastify";
import { useTranslation } from "react-i18next";
import { IconButton, Typography } from "@mui/material";
interface UploadFileDialogProps {
    icon_only?: boolean;
}

export function UploadFileDialog({ icon_only = false }: UploadFileDialogProps) {
    const [files, setFiles] = useState<File[]>([]);
    const [open, setOpen] = useState<boolean>(false);
    const dispatch = useAppDispatch();
    const { t } = useTranslation();

    const addFiles = (filesToUpload: File[]) =>
        setFiles([...files, ...filesToUpload]);
    const removeFile = (file: File) =>
        setFiles(files.filter((f) => f !== file));

    const upload = () => {
        uploadFiles(files);
    };

    const handleClose = (_: unknown, reason: string) => {
        if (reason && reason == "backdropClick") {
            return;
        }
        cancel();
    };

    const cancel = () => {
        setOpen(false);
        setFiles([]);
    };

    const uploadFiles = (filesToUpload: File[]) => {
        async function uploadAllFiles() {
            dispatch(startLoadingIndicator());
            try {
                await Promise.all(
                    filesToUpload.map((file) => uploadFile(file)),
                );
            } catch (error) {
                toast.error("Cannot upload files. Reason: " + error);
            }
            toast.success("Files successfully uploaded");
            dispatch(setBackgroundTaskSpinnerActive());
            dispatch(stopLoadingIndicator());
        }
        uploadAllFiles();
        cancel();
    };

    return (
        <>
            {icon_only ? (
                <IconButton
                    onClick={() => setOpen(true)}
                    title={t("uploadFileDialog.uploadButton")}
                >
                    <UploadFile />
                </IconButton>
            ) : (
                <Button
                    variant="contained"
                    startIcon={<UploadFile />}
                    color="secondary"
                    onClick={() => setOpen(true)}
                    fullWidth={true}
                >
                    {t("uploadFileDialog.uploadButton")}
                </Button>
            )}

            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>
                    <Typography>{t("uploadFileDialog.title")}</Typography>
                    <IconButton
                        aria-label="close"
                        onClick={cancel}
                        title={t("common.close")}
                        sx={{
                            position: "absolute",
                            right: 8,
                            top: 8,
                            color: (theme) => theme.palette.grey[500],
                        }}
                    >
                        <Close />
                    </IconButton>
                </DialogTitle>
                <DialogContent>
                    <div>
                        <Dropzone onDrop={addFiles} multiple={true}>
                            {({
                                getRootProps,
                                getInputProps,
                                isDragActive,
                            }) => (
                                <div
                                    {...getRootProps()}
                                    style={{
                                        width: "100%",
                                        height: "30vh",
                                        borderWidth: "2px",
                                        borderColor: isDragActive
                                            ? "#31312e"
                                            : "#BDBDBD",
                                        borderStyle: "dashed",
                                        borderRadius: "5px",
                                        backgroundColor: "#E0E0E0",
                                        cursor: "pointer",
                                    }}
                                >
                                    <div
                                        className={styles.uploadFileDropzone}
                                        style={{}}
                                    >
                                        <div
                                            className={
                                                styles.uploadFileDropzoneText
                                            }
                                        >
                                            {t("uploadFileDialog.dropzoneText")}
                                        </div>
                                        <UploadIcon
                                            className={
                                                styles.uploadFileDropzoneIcon
                                            }
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
                    </div>
                </DialogContent>
                <DialogActions>
                    <Button
                        startIcon={<Close />}
                        variant="outlined"
                        color="secondary"
                        onClick={cancel}
                    >
                        {t("common.cancel")}
                    </Button>
                    <Button
                        startIcon={<UploadFile />}
                        variant="contained"
                        disabled={files.length === 0}
                        onClick={upload}
                    >
                        {t("uploadFileDialog.uploadButton")}
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
}
