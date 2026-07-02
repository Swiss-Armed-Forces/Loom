import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import {
    Box,
    IconButton,
    InputBase,
    Stack,
    Typography,
    styled,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { DialogProps } from "@app/slices/commonSlice";

import { DialogBase } from "../DialogBase";

const StyledInputBase = styled(InputBase)(() => ({
    color: "inherit",
    borderRadius: "0.3rem",
    backgroundColor: "rgba(0, 0, 0, 0.08)",
    width: "100%",
    fontFamily: "monospace",
}));

interface EncryptionKeyInfoDialogProps extends DialogProps {
    encryptionKey: string;
}

export const EncryptionKeyInfoDialog = ({
    id,
    onClose,
    isTop,
    encryptionKey,
}: EncryptionKeyInfoDialogProps) => {
    const { t } = useTranslation();

    const handleCopy = () => {
        navigator.clipboard.writeText(encryptionKey).then(() => {
            toast.success(t("archives.encryptionKeyCopied"));
        });
    };

    return (
        <DialogBase
            id={id}
            onClose={onClose}
            isTop={isTop}
            title={t("archives.encryptionKeyInfoTitle")}
        >
            <Stack spacing={2}>
                <Typography variant="body2">
                    {t("archives.encryptionKeyInfoDescription")}
                </Typography>
                <Typography variant="body2">
                    {t("archives.encryptionKeyInfoSyncNote")}
                </Typography>
                <StyledInputBase
                    endAdornment={
                        <IconButton
                            size="small"
                            onClick={handleCopy}
                            sx={{ mr: 0.5 }}
                            title={t("common.copy")}
                        >
                            <ContentCopyIcon fontSize="small" />
                        </IconButton>
                    }
                    value={encryptionKey}
                    inputProps={{
                        "aria-label": t("archives.encryptionKeyInfoTitle"),
                        readOnly: true,
                        style: {
                            textAlign: "center",
                            padding: "8px 12px",
                            fontFamily: "monospace",
                        },
                    }}
                />
                <Box />
            </Stack>
        </DialogBase>
    );
};
