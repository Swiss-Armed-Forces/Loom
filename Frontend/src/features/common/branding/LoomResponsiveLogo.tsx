import { useMediaQuery } from "@mui/material";
import { useTranslation } from "react-i18next";

import LoomLogoCompact from "./loom-logo-compact.svg?react";
import LoomLogoFull from "./loom-logo-full-contour.svg?react";

export const LoomResponsiveLogo = () => {
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
};
