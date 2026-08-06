import { Download } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";

import { RenderedFile } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { selectSuppressDownloadWarning } from "@app/slices/searchSlice";
import { webApiGetFile } from "@features/common/urls";
import { DialogType } from "@features/common/utils/enums";

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

    const handleClick = () => {
        if (suppressWarning) {
            window.open(webApiGetFile(fileId), "_blank", "noopener,noreferrer");
        } else {
            dispatch(
                openDialog({
                    id: "",
                    type: DialogType.DownloadWarning,
                    props: { fileId, renderedFile },
                }),
            );
        }
    };

    return (
        <IconButton
            title={t("downloadWarning.title")}
            aria-label="download"
            onClick={handleClick}
        >
            <Download />
        </IconButton>
    );
};
