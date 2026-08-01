import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { IconButton, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { ActivityBarLayout } from "@features/common/components/ActivityBar/ActivityBarLayout";
import { DialogType } from "@features/common/utils/enums";

export const ArchivesActivityBar = () => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const handleClick = () => {
        dispatch(openDialog({ id: "", type: DialogType.ImportArchive }));
    };

    return (
        <ActivityBarLayout
            top={
                <Tooltip title={t("archives.importButton")} placement="right">
                    <IconButton
                        onClick={handleClick}
                        size="medium"
                        data-tour="archive-upload"
                        sx={{
                            bgcolor: "primary.main",
                            color: "primary.contrastText",
                            "&:hover": { bgcolor: "primary.dark" },
                        }}
                    >
                        <CloudUploadIcon />
                    </IconButton>
                </Tooltip>
            }
        />
    );
};
