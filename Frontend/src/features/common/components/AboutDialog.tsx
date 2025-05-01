import { Close } from "@mui/icons-material";
import {
    Dialog,
    DialogContent,
    DialogTitle,
    IconButton,
    Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

interface AboutDialogProps {
    open: boolean;
    closeDialog: () => void;
}

export function AboutDialog({ open, closeDialog }: AboutDialogProps) {
    const [licenseText, setLicenseText] = useState<string[]>([]);
    const { t } = useTranslation();

    useEffect(() => {
        const fetchFile = async () => {
            fetch("/" + t("about.license"))
                .then((r) => r.text())
                .then((text) => setLicenseText(text.split("\n")))
                .catch((err) => console.log(err));
        };

        fetchFile();
    }, [t]);

    return (
        <Dialog open={open}>
            <DialogTitle>
                <Typography>
                    <b>{t("about.titleDialog")}</b>
                </Typography>
                <IconButton
                    aria-label="close"
                    onClick={closeDialog}
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
            <DialogContent>
                <div>
                    <p>
                        {t("about.linkTitle")}
                        <a
                            href={t("about.link")}
                            target="_blank"
                            rel="noreferrer"
                        >
                            {t("about.link")}
                        </a>
                    </p>
                    {licenseText.map((text, index) => (
                        <p key={index}>{text}</p>
                    ))}
                    <p>
                        {t("about.downloadTitle")}
                        <a href={"/" + t("about.license")} download>
                            {t("about.license")}
                        </a>
                    </p>
                    <p>
                        {t("about.downloadTitle")}
                        <a href={"/" + t("about.thirdParty")} download>
                            {t("about.thirdParty")}
                        </a>
                    </p>
                </div>
            </DialogContent>
        </Dialog>
    );
}
