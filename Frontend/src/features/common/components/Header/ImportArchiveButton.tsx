import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { Button, IconButton, Tooltip, useMediaQuery } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";

export const ImportArchiveButton = () => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const isMobile = useMediaQuery("(max-width:600px)");

    const handleClick = () => {
        dispatch(openDialog({ id: "", type: DialogType.ImportArchive }));
    };

    return isMobile ? (
        <Tooltip title={t("archives.importButton")}>
            <IconButton onClick={handleClick} sx={{ color: "white" }}>
                <CloudUploadIcon />
            </IconButton>
        </Tooltip>
    ) : (
        <Button
            variant="outlined"
            startIcon={<CloudUploadIcon />}
            onClick={handleClick}
            sx={{ color: "white", borderColor: "white" }}
        >
            {t("archives.importButton")}
        </Button>
    );
};
