import { useMediaQuery } from "@mui/material";
import { forwardRef, useEffect, useImperativeHandle, useState } from "react";
import { useTranslation } from "react-i18next";

import LoomLogoCompact from "./loom-logo-compact.svg?react";
import LoomLogoFull from "./loom-logo-full-contour.svg?react";
import styles from "./LoomResponsiveLogo.module.css";

const BLINK_DURATION_MS = 500;

const randomTriggerDelay = () => (1 + Math.random() * 3) * 60 * 60 * 1000; // randomly between 1 and 4 hours

export interface LoomResponsiveLogoHandle {
    triggerAnimation: () => void;
}

export const LoomResponsiveLogo = forwardRef<LoomResponsiveLogoHandle>(
    (_, ref) => {
        const { t } = useTranslation();
        const isMobile = useMediaQuery("(max-width: 1100px)");
        const [blinking, setBlinking] = useState(false);

        const now = new Date();
        const month = now.getMonth();
        const day = now.getDate();
        // Show from July 26 through August 1 (Swiss National Day)
        const isSwissNationalDay =
            (month === 6 && day >= 26) || (month === 7 && day === 1);

        const triggerBlink = () => {
            setBlinking(true);
            setTimeout(() => setBlinking(false), BLINK_DURATION_MS);
        };

        useImperativeHandle(ref, () => ({ triggerAnimation: triggerBlink }));

        useEffect(() => {
            let timeoutId: ReturnType<typeof setTimeout>;

            const scheduleNext = () => {
                timeoutId = setTimeout(() => {
                    triggerBlink();
                    timeoutId = setTimeout(scheduleNext, randomTriggerDelay());
                }, randomTriggerDelay());
            };

            scheduleNext();
            return () => clearTimeout(timeoutId);
        }, []);

        return (
            <div
                title={
                    isSwissNationalDay
                        ? "🇨🇭 Happy Swiss National Day! Grüessech, Bonjour, Buongiorno, Allegra — 1. August 1291 🏔️"
                        : t("header.appName")
                }
                className={blinking ? styles.animBlink : undefined}
                style={{
                    position: "relative",
                    display: "inline-flex",
                    alignItems: "center",
                    overflow: "visible",
                }}
            >
                {isMobile ? (
                    <LoomLogoCompact
                        style={{ maxWidth: "60px", maxHeight: "30px" }}
                    />
                ) : (
                    <LoomLogoFull
                        style={{ maxWidth: "100px", maxHeight: "40px" }}
                    />
                )}
                {isSwissNationalDay && (
                    <svg
                        viewBox="0 0 30 22"
                        width="36"
                        height="26"
                        style={{
                            position: "absolute",
                            top: "-16px",
                            left: isMobile ? "30%" : "34%",
                            pointerEvents: "none",
                            overflow: "visible",
                            transform: "rotate(15deg)",
                            transformOrigin: "bottom center",
                        }}
                        aria-hidden="true"
                    >
                        {/* Feather (behind hat) */}
                        <path
                            d="M 22.5,15 C 29,9 30,1 26.5,0 C 27.5,4 24,9 21.5,13"
                            fill="#e8e8d0"
                            stroke="#b8b8a0"
                            strokeWidth="0.4"
                        />
                        {/* Crown */}
                        <path
                            d="M 6,17 C 6,17 7,3 15,2 C 23,3 24,17 24,17 Z"
                            fill="#3d2008"
                            stroke="#8b6040"
                            strokeWidth="0.8"
                        />
                        {/* Brim */}
                        <ellipse
                            cx="15"
                            cy="17"
                            rx="14"
                            ry="3"
                            fill="#3d2008"
                            stroke="#8b6040"
                            strokeWidth="0.8"
                        />
                        {/* Hat band (red) */}
                        <rect
                            x="6"
                            y="12.5"
                            width="18"
                            height="2.8"
                            fill="#cc0000"
                            rx="0.4"
                        />
                        {/* Swiss cross: horizontal bar */}
                        <rect
                            x="13"
                            y="13.45"
                            width="4"
                            height="0.9"
                            fill="white"
                        />
                        {/* Swiss cross: vertical bar */}
                        <rect
                            x="14.55"
                            y="12.7"
                            width="0.9"
                            height="2.4"
                            fill="white"
                        />
                    </svg>
                )}
            </div>
        );
    },
);

LoomResponsiveLogo.displayName = "LoomResponsiveLogo";
