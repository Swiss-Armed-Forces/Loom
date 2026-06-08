import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import KeyIcon from "@mui/icons-material/Key";
import { Box, IconButton, InputBase, styled, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getEncryptionKey } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";

const StyledInputBase = styled(InputBase)(() => ({
    color: "inherit",
    borderRadius: "0.3rem",
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    width: "100%",
    fontFamily: "monospace",
}));

export const ArchiveEncryptionKeyDisplay = () => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const [encryptionKey, setEncryptionKey] = useState<string | null>(null);
    useEffect(() => {
        getEncryptionKey().then(setEncryptionKey);
    }, []);

    if (encryptionKey === null) {
        return null;
    }

    const handleInfo = () => {
        dispatch(
            openDialog({
                id: "encryption-key-info",
                type: DialogType.EncryptionKeyInfo,
                props: { encryptionKey },
            }),
        );
    };

    return (
        <StyledInputBase
            startAdornment={
                <Box
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        pl: 1,
                        pr: 0.5,
                        py: 1,
                        gap: 0.5,
                        whiteSpace: "nowrap",
                    }}
                >
                    <KeyIcon fontSize="small" />
                    <Typography variant="caption" sx={{ opacity: 0.75 }}>
                        {t("archives.encryptionKeyTitle")}
                    </Typography>
                </Box>
            }
            endAdornment={
                <IconButton
                    color="inherit"
                    size="small"
                    onClick={handleInfo}
                    sx={{ mr: 0.5 }}
                    title={t("archives.encryptionKeyInfoTitle")}
                >
                    <InfoOutlinedIcon fontSize="small" />
                </IconButton>
            }
            value={encryptionKey}
            inputProps={{
                "aria-label": t("archives.encryptionKeyTitle"),
                readOnly: true,
                style: { textAlign: "center" },
            }}
        />
    );
};
