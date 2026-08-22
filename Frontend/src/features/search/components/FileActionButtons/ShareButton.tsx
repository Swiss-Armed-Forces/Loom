import { Share } from "@mui/icons-material";
import { t } from "i18next";
import { toast } from "react-toastify";

import { FileActionButtonBase } from "./FileActionButtonBase";

interface ShareProps {
    fileId: string;
    disableTooltip?: boolean;
}

export const ShareButton = ({ fileId, disableTooltip = false }: ShareProps) => {
    const handleClick = () => {
        const url = new URL(location.toString());
        url.hash = fileId;
        if (window.isSecureContext) {
            navigator.clipboard
                .writeText(url.toString())
                .then(() =>
                    toast.success(t("generalSearchView.shareContent.success")),
                )
                .catch(() =>
                    toast.error(t("generalSearchView.shareContent.failure")),
                );
        } else {
            toast.error(t("generalSearchView.shareContent.noSecureContext"));
        }
    };

    return (
        <FileActionButtonBase
            icon={<Share />}
            label={t("generalSearchView.shareContent.title")}
            onClick={handleClick}
            iconOnly
            disableTooltip={disableTooltip}
            ariaLabel="share"
        />
    );
};
