import { Close } from "@mui/icons-material";
import { Dialog, DialogContent, DialogTitle, IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";
import { webApiGetFilePreview } from "../../common/urls";
import styles from "./ImageDetailDialog.module.css";

interface ImageDetailDialogProps {
    imageHashToShow: string | null;
    onClose: () => void;
}

export function ImageDetailDialog({
    imageHashToShow,
    onClose,
}: ImageDetailDialogProps) {
    const { t } = useTranslation();

    return (
        <Dialog
            open={!!imageHashToShow}
            onClose={onClose}
            maxWidth="xl"
            fullWidth={true}
        >
            <DialogTitle>
                {t("imageDetailDialog.title")}
                <IconButton
                    aria-label="close"
                    onClick={onClose}
                    title={t("common.close")}
                    sx={{
                        position: "absolute",
                        right: 8,
                        top: 8,
                        color: (theme) => theme.palette.grey[500],
                    }}
                >
                    <Close />
                </IconButton>
            </DialogTitle>
            <DialogContent className={styles.content}>
                {!!imageHashToShow && (
                    <img
                        src={webApiGetFilePreview(imageHashToShow)}
                        alt={t("imageDetailDialog.imgAlt")}
                        className={styles.imageDetailDialogImg}
                    />
                )}
            </DialogContent>
        </Dialog>
    );
}
