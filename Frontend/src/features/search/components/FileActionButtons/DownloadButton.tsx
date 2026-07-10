import {
    Description,
    Download,
    Image,
    OpenInBrowser,
    WarningAmber,
} from "@mui/icons-material";
import {
    Alert,
    Box,
    Button,
    Checkbox,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    FormControlLabel,
    IconButton,
    Tooltip,
    Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { RenderedFile } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectSuppressDownloadWarning,
    setSuppressDownloadWarning,
} from "@app/slices/searchSlice";

import { webApiGetFile, webApiGetFileRendered } from "../../../common/urls";

interface DownloadButtonProps {
    fileId: string;
    renderedFile?: RenderedFile;
}

export const DownloadButton = ({
    fileId,
    renderedFile,
}: DownloadButtonProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const suppressWarning = useAppSelector(selectSuppressDownloadWarning);
    const [open, setOpen] = useState(false);
    const [dontShowAgain, setDontShowAgain] = useState(false);

    const handleClick = () => {
        if (suppressWarning) {
            window.open(webApiGetFile(fileId), "_blank", "noopener,noreferrer");
        } else {
            setDontShowAgain(false);
            setOpen(true);
        }
    };

    const handleConfirm = () => {
        if (dontShowAgain) {
            dispatch(setSuppressDownloadWarning(true));
        }
        setOpen(false);
        window.open(webApiGetFile(fileId), "_blank", "noopener,noreferrer");
    };

    const handleCancel = () => {
        setOpen(false);
    };

    const renderedOptions: {
        label: string;
        icon: React.ReactNode;
        url: string;
    }[] = [];
    if (renderedFile?.officePdfFileId) {
        renderedOptions.push({
            label: t("downloadWarning.renderedPdfOffice"),
            icon: <Description fontSize="small" />,
            url: webApiGetFileRendered(fileId, renderedFile.officePdfFileId),
        });
    }
    if (renderedFile?.browserPdfFileId) {
        renderedOptions.push({
            label: t("downloadWarning.renderedPdfBrowser"),
            icon: <OpenInBrowser fontSize="small" />,
            url: webApiGetFileRendered(fileId, renderedFile.browserPdfFileId),
        });
    }
    if (renderedFile?.imageFileId) {
        renderedOptions.push({
            label: t("downloadWarning.renderedImage"),
            icon: <Image fontSize="small" />,
            url: webApiGetFileRendered(fileId, renderedFile.imageFileId),
        });
    }

    return (
        <>
            <IconButton
                title={t("downloadWarning.title")}
                aria-label="download"
                onClick={handleClick}
            >
                <Download />
            </IconButton>

            <Dialog open={open} onClose={handleCancel} maxWidth="sm" fullWidth>
                <DialogTitle
                    sx={{ display: "flex", alignItems: "center", gap: 1 }}
                >
                    <WarningAmber color="warning" />
                    {t("downloadWarning.title")}
                </DialogTitle>
                <DialogContent
                    sx={{ display: "flex", flexDirection: "column", gap: 2 }}
                >
                    <Typography variant="body2">
                        {t("downloadWarning.body")}
                    </Typography>

                    <Alert
                        severity="info"
                        variant="outlined"
                        sx={{ alignItems: "flex-start" }}
                    >
                        <Typography variant="body2">
                            {t(
                                renderedOptions.length > 0
                                    ? "downloadWarning.safeAlternativeWithOptions"
                                    : "downloadWarning.safeAlternative",
                            )}
                        </Typography>
                        {renderedOptions.length > 0 && (
                            <Box
                                sx={{
                                    mt: 1.5,
                                    display: "flex",
                                    flexWrap: "wrap",
                                    gap: 1,
                                }}
                            >
                                {renderedOptions.map(({ label, icon, url }) => (
                                    <Tooltip key={label} title={label}>
                                        <Button
                                            component="a"
                                            href={url}
                                            download
                                            size="small"
                                            variant="outlined"
                                            color="info"
                                            startIcon={icon}
                                            sx={{ textTransform: "none" }}
                                        >
                                            {label}
                                        </Button>
                                    </Tooltip>
                                ))}
                            </Box>
                        )}
                    </Alert>

                    <Divider />

                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={dontShowAgain}
                                onChange={(e) =>
                                    setDontShowAgain(e.target.checked)
                                }
                                size="small"
                            />
                        }
                        label={
                            <Typography variant="body2" color="text.secondary">
                                {t("downloadWarning.dontShowAgain")}
                            </Typography>
                        }
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCancel} color="inherit">
                        {t("common.cancel")}
                    </Button>
                    <Button
                        onClick={handleConfirm}
                        color="warning"
                        variant="contained"
                        startIcon={<Download />}
                    >
                        {t("downloadWarning.confirm")}
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
};
