import { useTranslation } from "react-i18next";
import LoomLogoSvg from "./loom-logo-text.svg?react";

export function LoomResponsiveLogo(props: { color: string }) {
    const { t } = useTranslation();
    return (
        <div title={t("header.appName")}>
            <LoomLogoSvg fill={props.color} />
        </div>
    );
}
