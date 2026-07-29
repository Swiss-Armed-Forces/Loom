import FileIcon from "@mui/icons-material/Attachment";
import UploadIcon from "@mui/icons-material/CloudUpload";
import { Alert, Avatar, Chip } from "@mui/material";
import Dropzone from "react-dropzone";
import { useTranslation } from "react-i18next";

import styles from "./FileDropzone.module.css";

const LARGE_FILE_THRESHOLD_BYTES = 500 * 1024 * 1024; // 500 MiB

interface FileDropzoneProps {
    multiple?: boolean;
    accept?: Record<string, string[]>;
    dropzoneText: string;
    files: File[];
    onFilesChange: (files: File[]) => void;
    disabled?: boolean;
}

export const FileDropzone = ({
    multiple = true,
    accept,
    dropzoneText,
    files,
    onFilesChange,
    disabled = false,
}: FileDropzoneProps) => {
    const { t } = useTranslation();

    const hasLargeFile = files.some((f) => f.size > LARGE_FILE_THRESHOLD_BYTES);

    const handleDrop = (droppedFiles: File[]) => {
        onFilesChange([...files, ...droppedFiles]);
    };

    const removeFile = (file: File) => {
        onFilesChange(files.filter((f) => f !== file));
    };

    return (
        <>
            <Dropzone
                onDrop={handleDrop}
                multiple={multiple}
                accept={accept}
                disabled={disabled}
            >
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
                            cursor: disabled ? "default" : "pointer",
                            boxSizing: "border-box",
                        }}
                    >
                        <div className={styles.dropzone}>
                            <div className={styles.dropzoneText}>
                                {dropzoneText}
                            </div>
                            <UploadIcon className={styles.dropzoneIcon} />
                            <input {...getInputProps()} />
                        </div>
                    </div>
                )}
            </Dropzone>
            {hasLargeFile && (
                <Alert severity="warning">
                    {t("uploadFileDialog.largeFileWarning")}
                </Alert>
            )}
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
                            onDelete={() => removeFile(file)}
                        />
                    ))}
                </div>
            )}
        </>
    );
};
