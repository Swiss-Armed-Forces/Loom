import { TourStep } from "./types";

type TargetWaitResult = "found" | "missing" | "cancelled";

export type StepResolution =
    | { kind: "found"; index: number }
    | { kind: "exhausted" }
    | { kind: "required-missing"; step: TourStep }
    | { kind: "cancelled" };

interface StepResolutionRequest {
    activateStep: (step: TourStep) => void;
    direction: 1 | -1;
    signal: AbortSignal;
    startIndex: number;
    steps: readonly TourStep[];
}

export const targetExists = (step: TourStep): boolean => {
    try {
        return document.querySelector(step.target.selector) !== null;
    } catch {
        return false;
    }
};

export const waitForTourTarget = (
    step: TourStep,
    signal: AbortSignal,
): Promise<TargetWaitResult> => {
    if (signal.aborted) return Promise.resolve("cancelled");
    if (targetExists(step)) return Promise.resolve("found");

    const timeoutMs = step.waitForElementMs ?? 0;
    if (timeoutMs <= 0) return Promise.resolve("missing");

    return new Promise((resolve) => {
        let settled = false;
        const finish = (result: TargetWaitResult) => {
            if (settled) return;
            settled = true;
            observer.disconnect();
            window.clearTimeout(timeout);
            signal.removeEventListener("abort", handleAbort);
            resolve(result);
        };
        const observer = new MutationObserver(() => {
            if (targetExists(step)) finish("found");
        });
        const timeout = window.setTimeout(() => finish("missing"), timeoutMs);
        const handleAbort = () => finish("cancelled");

        signal.addEventListener("abort", handleAbort, { once: true });
        observer.observe(document.documentElement, {
            attributes: true,
            childList: true,
            subtree: true,
        });
    });
};

export const resolveAvailableTourStep = async ({
    activateStep,
    direction,
    signal,
    startIndex,
    steps,
}: StepResolutionRequest): Promise<StepResolution> => {
    for (
        let index = startIndex;
        index >= 0 && index < steps.length;
        index += direction
    ) {
        const step = steps[index];
        activateStep(step);
        const target = await waitForTourTarget(step, signal);

        if (target === "cancelled") return { kind: "cancelled" };
        if (target === "found") return { kind: "found", index };
        if (step.skipIfMissing === false) {
            return { kind: "required-missing", step };
        }
    }

    return { kind: "exhausted" };
};
