import { afterEach, describe, expect, it, vi } from "vitest";

import {
    resolveAvailableTourStep,
    targetExists,
    waitForTourTarget,
} from "./targets";
import { TourStep } from "./types";

const step = (id: string, overrides: Partial<TourStep> = {}): TourStep => ({
    id,
    target: { selector: `[data-tour="${id}"]` },
    titleKey: `${id}.title`,
    descriptionKey: `${id}.description`,
    ...overrides,
});

afterEach(() => {
    document.body.replaceChildren();
});

describe("tour target resolution", () => {
    it("finds an existing target immediately", async () => {
        document.body.innerHTML = '<div data-tour="welcome"></div>';
        const welcome = step("welcome");

        expect(targetExists(welcome)).toBe(true);
        await expect(
            waitForTourTarget(welcome, new AbortController().signal),
        ).resolves.toBe("found");
    });

    it("waits for a target added by a DOM mutation", async () => {
        const delayed = step("delayed", { waitForElementMs: 100 });
        const result = waitForTourTarget(delayed, new AbortController().signal);

        const target = document.createElement("div");
        target.dataset.tour = "delayed";
        document.body.append(target);

        await expect(result).resolves.toBe("found");
    });

    it("cancels a pending target wait", async () => {
        const controller = new AbortController();
        const result = waitForTourTarget(
            step("pending", { waitForElementMs: 100 }),
            controller.signal,
        );

        controller.abort();

        await expect(result).resolves.toBe("cancelled");
    });

    it("skips optional targets in either direction", async () => {
        document.body.innerHTML = '<div data-tour="available"></div>';
        const steps = [step("available"), step("missing")];
        const activateStep = vi.fn();

        await expect(
            resolveAvailableTourStep({
                activateStep,
                direction: -1,
                signal: new AbortController().signal,
                startIndex: 1,
                steps,
            }),
        ).resolves.toEqual({ kind: "found", index: 0 });
        expect(activateStep).toHaveBeenCalledTimes(2);
    });

    it("reports a required missing target", async () => {
        const required = step("required", { skipIfMissing: false });

        await expect(
            resolveAvailableTourStep({
                activateStep: vi.fn(),
                direction: 1,
                signal: new AbortController().signal,
                startIndex: 0,
                steps: [required],
            }),
        ).resolves.toEqual({ kind: "required-missing", step: required });
    });

    it("reports exhaustion when no optional target exists", async () => {
        await expect(
            resolveAvailableTourStep({
                activateStep: vi.fn(),
                direction: 1,
                signal: new AbortController().signal,
                startIndex: 0,
                steps: [step("missing")],
            }),
        ).resolves.toEqual({ kind: "exhausted" });
    });
});
