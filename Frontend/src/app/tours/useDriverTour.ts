import { useMediaQuery } from "@mui/material";
import { driver, DriveStep, Driver } from "driver.js";
import "driver.js/dist/driver.css";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { filterTourSteps } from "./responsive";
import { TourOutcome, TourStep } from "./types";
import "./tour.css";

interface DriverTourController {
    dismiss: () => void;
    isActive: boolean;
    start: () => boolean;
}

const targetExists = (step: TourStep): boolean => {
    try {
        return document.querySelector(step.target.selector) !== null;
    } catch {
        return false;
    }
};

export const useDriverTour = (
    configuredSteps: readonly TourStep[],
    onFinish: (outcome: TourOutcome) => void,
): DriverTourController => {
    const { t } = useTranslation();
    const isMobile = useMediaQuery("(max-width:600px)");
    const driverRef = useRef<Driver | null>(null);
    const [isActive, setIsActive] = useState(false);

    const start = useCallback((): boolean => {
        driverRef.current?.destroy();

        const steps = filterTourSteps(configuredSteps, isMobile);
        if (steps.length === 0 || !steps.some(targetExists)) {
            onFinish("dismissed");
            setIsActive(false);
            return false;
        }

        let finalized = false;
        const finalize = (outcome: TourOutcome) => {
            if (finalized) return;
            finalized = true;
            onFinish(outcome);
            driverRef.current = null;
            setIsActive(false);
        };

        const driveSteps: DriveStep[] = steps.map((step) => ({
            element: step.target.selector,
            popover: {
                title: t(step.titleKey),
                description: t(step.descriptionKey),
                side: step.side,
                align: step.align,
            },
            disableActiveInteraction: true,
            skipMissingElement: step.skipIfMissing ?? true,
            waitForElement: step.waitForElementMs ?? 1_000,
        }));

        const driverInstance = driver({
            animate: !window.matchMedia("(prefers-reduced-motion: reduce)")
                .matches,
            allowClose: true,
            allowKeyboardControl: true,
            allowScroll: true,
            disableActiveInteraction: true,
            overlayClickBehavior: "close",
            popoverClass: "loom-tour-popover",
            showButtons: ["previous", "next", "close"],
            showProgress: true,
            progressText: t("tour.controls.progress", {
                current: "{{current}}",
                total: "{{total}}",
            }),
            prevBtnText: t("tour.controls.previous"),
            nextBtnText: t("tour.controls.next"),
            doneBtnText: t("tour.controls.done"),
            skipMissingElement: true,
            smoothScroll: true,
            steps: driveSteps,
            waitForElement: 1_000,
            onPopoverRender: ({ closeButton }) => {
                closeButton.setAttribute(
                    "aria-label",
                    t("tour.controls.close"),
                );
                closeButton.title = t("tour.controls.close");
            },
            onCloseClick: (_element, _step, { driver: instance }) => {
                finalize("dismissed");
                instance.destroy();
            },
            onDoneClick: (_element, _step, { driver: instance }) => {
                finalize("completed");
                instance.destroy();
            },
            onDestroyed: () => finalize("dismissed"),
        });

        driverRef.current = driverInstance;
        setIsActive(true);
        driverInstance.drive();
        return true;
    }, [configuredSteps, isMobile, onFinish, t]);

    const dismiss = useCallback(() => driverRef.current?.destroy(), []);

    useEffect(() => () => driverRef.current?.destroy(), []);

    return { dismiss, isActive, start };
};
