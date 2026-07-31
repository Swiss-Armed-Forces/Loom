import { useMediaQuery } from "@mui/material";
import { driver, DriveStep, Driver } from "driver.js";
import "driver.js/dist/driver.css";
import { useCallback, useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { useTranslation } from "react-i18next";

import { filterTourSteps } from "./responsive";
import { resolveAvailableTourStep, targetExists } from "./targets";
import {
    TourEndReason,
    TourFinishResult,
    TourOutcome,
    TourStartRequest,
    TourStep,
} from "./types";
import "./tour.css";

interface DriverTourController {
    dismiss: () => void;
    isActive: boolean;
    start: (request: TourStartRequest) => void;
}

type TourStepNextHandler = (stepId: string) => Promise<boolean> | boolean;

export const useDriverTour = (
    onFinish: (result: TourFinishResult) => void,
    onStepChange?: (stepId: string) => void,
    onStepNext?: TourStepNextHandler,
): DriverTourController => {
    const { t } = useTranslation();
    const isMobile = useMediaQuery("(max-width:600px)");
    const driverRef = useRef<Driver | null>(null);
    const dismissRef = useRef<(() => void) | null>(null);
    const [isActive, setIsActive] = useState(false);

    const start = useCallback(
        ({ mode, steps: requestedSteps }: TourStartRequest): void => {
            dismissRef.current?.();
            const steps = filterTourSteps(requestedSteps, isMobile);
            if (steps.length === 0) {
                onFinish({
                    acknowledgedSteps: [],
                    mode,
                    outcome: "dismissed",
                    reason: "no-available-targets",
                });
                setIsActive(false);
                return;
            }

            const controller = new AbortController();
            let driverInstance: Driver | null = null;
            let finalized = false;
            let stepActionPending = false;
            const finalize = (
                outcome: TourOutcome,
                reason: TourEndReason,
                acknowledgedSteps = steps,
            ) => {
                if (finalized) return;
                finalized = true;
                controller.abort();
                onFinish({ acknowledgedSteps, mode, outcome, reason });
                if (driverRef.current === driverInstance) {
                    driverRef.current = null;
                }
                setIsActive(false);
            };

            const dismissCurrentTour = () => {
                finalize("dismissed", "user-dismissed");
                driverInstance?.destroy();
            };
            dismissRef.current = dismissCurrentTour;

            const activateStep = (step: TourStep) => {
                flushSync(() => {
                    setIsActive(true);
                    onStepChange?.(step.id);
                });
            };

            const findAvailableStep = (startIndex: number, direction: 1 | -1) =>
                resolveAvailableTourStep({
                    activateStep,
                    direction,
                    signal: controller.signal,
                    startIndex,
                    steps,
                });

            const abortForMissingRequiredStep = (step: TourStep) => {
                console.warn(
                    `Required tour target did not appear for step "${step.id}": ${step.target.selector}`,
                );
                finalize(
                    "dismissed",
                    "required-target-missing",
                    steps.filter(({ id }) => id !== step.id),
                );
                driverInstance?.destroy();
            };

            const withPendingButton = async (
                selector: string,
                action: () => Promise<void>,
            ) => {
                if (stepActionPending) return;
                stepActionPending = true;
                const button =
                    document.querySelector<HTMLButtonElement>(selector);
                if (button) button.disabled = true;
                try {
                    await action();
                } finally {
                    stepActionPending = false;
                    if (button) button.disabled = false;
                }
            };

            const advance = async (index: number, instance: Driver) =>
                withPendingButton(".driver-popover-next-btn", async () => {
                    if ((await onStepNext?.(steps[index].id)) === false) return;

                    const next = await findAvailableStep(index + 1, 1);
                    if (next.kind === "cancelled") return;
                    if (next.kind === "required-missing") {
                        abortForMissingRequiredStep(next.step);
                        return;
                    }
                    if (next.kind === "exhausted") {
                        finalize("completed", "completed");
                        instance.destroy();
                        return;
                    }

                    instance.moveTo(next.index);
                });

            const moveBack = async (index: number, instance: Driver) =>
                withPendingButton(".driver-popover-prev-btn", async () => {
                    const previous = await findAvailableStep(index - 1, -1);
                    if (previous.kind === "cancelled") return;
                    if (previous.kind === "required-missing") {
                        abortForMissingRequiredStep(previous.step);
                        return;
                    }
                    if (previous.kind === "exhausted") {
                        activateStep(steps[index]);
                        return;
                    }

                    instance.moveTo(previous.index);
                });

            const driveSteps: DriveStep[] = steps.map((step, index) => ({
                element: step.target.selector,
                popover: {
                    title: t(step.titleKey),
                    description: t(step.descriptionKey),
                    side: step.side,
                    align: step.align,
                    doneBtnText: step.doneButtonKey
                        ? t(step.doneButtonKey)
                        : undefined,
                    nextBtnText: step.nextButtonKey
                        ? t(step.nextButtonKey)
                        : undefined,
                    onNextClick: (_element, _driveStep, { driver: instance }) =>
                        advance(index, instance),
                    onDoneClick: (_element, _driveStep, { driver: instance }) =>
                        advance(index, instance),
                    ...(index > 0
                        ? {
                              onPrevClick: async (
                                  _element,
                                  _driveStep,
                                  { driver: instance },
                              ) => moveBack(index, instance),
                          }
                        : {}),
                },
                disableActiveInteraction: true,
                // Loom activates and resolves each target before moving Driver.js.
                // Driver-side skipping would run too early for scene-rendered targets.
                skipMissingElement: false,
                waitForElement: step.waitForElementMs ?? 1_000,
            }));

            if (mode === "full") {
                activateStep(steps[0]);
                if (
                    !steps.some(targetExists) &&
                    (steps[0].waitForElementMs ?? 0) <= 0 &&
                    !steps.some(({ skipIfMissing }) => skipIfMissing === false)
                ) {
                    finalize("dismissed", "no-available-targets");
                    return;
                }
            }

            void findAvailableStep(0, 1).then((first) => {
                if (first.kind === "cancelled") return;
                if (first.kind === "required-missing") {
                    abortForMissingRequiredStep(first.step);
                    return;
                }
                if (first.kind === "exhausted") {
                    finalize("dismissed", "no-available-targets");
                    return;
                }

                driverInstance = driver({
                    animate: !window.matchMedia(
                        "(prefers-reduced-motion: reduce)",
                    ).matches,
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
                    skipMissingElement: false,
                    smoothScroll: true,
                    steps: driveSteps,
                    waitForElement: 1_000,
                    onPopoverRender: (
                        { closeButton, footerButtons },
                        { index },
                    ) => {
                        closeButton.setAttribute(
                            "aria-label",
                            t("tour.controls.close"),
                        );
                        closeButton.title = t("tour.controls.close");

                        if (!steps[index ?? -1]?.showSkipButton) return;

                        const skipButton = document.createElement("button");
                        skipButton.type = "button";
                        skipButton.classList.add(
                            "driver-popover-footer-btn",
                            "loom-tour-skip-btn",
                        );
                        skipButton.textContent = t("tour.controls.skip");
                        skipButton.addEventListener(
                            "click",
                            dismissCurrentTour,
                        );
                        footerButtons.prepend(skipButton);
                    },
                    onCloseClick: dismissCurrentTour,
                    onDestroyed: () => finalize("dismissed", "user-dismissed"),
                });

                driverRef.current = driverInstance;
                driverInstance.drive(first.index);
            });
        },
        [isMobile, onFinish, onStepChange, onStepNext, t],
    );

    const dismiss = useCallback(() => dismissRef.current?.(), []);

    useEffect(() => () => dismissRef.current?.(), []);

    return { dismiss, isActive, start };
};
