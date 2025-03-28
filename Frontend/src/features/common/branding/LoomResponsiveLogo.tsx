import { useTranslation } from "react-i18next";
import { useMediaQuery } from "@mui/material";
import LoomLogoFull from "./loom-logo-full-contour.svg?react";
import LoomLogoCompact from "./loom-logo-compact.svg?react";

export function LoomResponsiveLogo() {
    const { t } = useTranslation();
    const isMobile = useMediaQuery("(max-width: 1100px)");

    return (
        <div title={t("header.appName")}>
            {isMobile ? (
                <LoomLogoCompact
                    style={{ maxWidth: "60px", maxHeight: "30px" }}
                />
            ) : (
                <LoomLogoFull
                    style={{ maxWidth: "200px", maxHeight: "80px" }}
                />
            )}
        </div>
    );
}
