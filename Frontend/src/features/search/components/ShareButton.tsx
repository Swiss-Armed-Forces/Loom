import { Share } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { t } from "i18next";
import { toast } from "react-toastify";

interface ShareProps {
    fileId: string;
}

export function ShareButton({ fileId }: ShareProps) {
    return (
        <IconButton
            aria-label="share"
            title={t("generalSearchView.shareContent.title")}
            onClick={() => {
                const url = new URL(location.toString());
                url.hash = fileId;
                // Navigator clipboard api needs secure context (https)
                if (window.isSecureContext) {
                    navigator.clipboard
                        .writeText(url.toString())
                        .then(() =>
                            toast.success(
                                t("generalSearchView.shareContent.success"),
                            ),
                        )
                        .catch(() =>
                            toast.error(
                                t("generalSearchView.shareContent.failure"),
                            ),
                        );
                } else {
                    toast.error(
                        t("generalSearchView.shareContent.noSecureContext"),
                    );
                }
            }}
        >
            <Share />
        </IconButton>
    );
}
