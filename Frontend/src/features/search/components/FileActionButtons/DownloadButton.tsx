import { Download } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

import { RenderedFile } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { selectSuppressDownloadWarning } from "@app/slices/searchSlice";
import { webApiGetFile } from "@features/common/urls";
import { DialogType } from "@features/common/utils/enums";

import { FileActionButtonBase } from "./FileActionButtonBase";

interface DownloadButtonProps {
    fileId: string;
    renderedFile?: RenderedFile;
    disableTooltip?: boolean;
}

export const DownloadButton = ({
    fileId,
    renderedFile,
    disableTooltip = false,
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
        <FileActionButtonBase
            icon={<Download />}
            label={t("downloadWarning.title")}
            onClick={handleClick}
            iconOnly
            disableTooltip={disableTooltip}
            ariaLabel="download"
        />
    );
};
