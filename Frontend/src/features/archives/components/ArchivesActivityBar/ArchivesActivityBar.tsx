import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { IconButton, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { ActivityBarLayout } from "@features/common/components/ActivityBar/ActivityBarLayout";
import activityBarStyles from "@features/common/components/ActivityBar/ActivityBarLayout.module.css";
import { DialogType } from "@features/common/utils/enums";

interface ArchivesActivityBarProps {
    position: "top" | "bottom";
}

export const ArchivesActivityBar = ({ position }: ArchivesActivityBarProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const handleClick = () => {
        dispatch(openDialog({ id: "", type: DialogType.ImportArchive }));
    };

    const uploadButton = (placement: "top" | "right") => (
        <Tooltip title={t("archives.importButton")} placement={placement}>
            <IconButton
                onClick={handleClick}
                size="medium"
                // Both positions carry it: only one of the two bars is ever
                // mounted, so tagging the mobile one alone would leave the
                // tour's upload step unable to resolve on a desktop.
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
    );

    if (position === "bottom") {
        return (
            <div
                className={activityBarStyles.activityBarBottom}
                style={{
                    borderTop: "1px solid",
                    borderColor: "var(--mui-palette-divider)",
                    paddingLeft: "0.5rem",
                }}
            >
                {uploadButton("top")}
            </div>
        );
    }

    return <ActivityBarLayout top={uploadButton("right")} />;
};
