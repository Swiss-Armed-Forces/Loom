import { describe, expect, it } from "vitest";

import { GLOBAL_TOUR_STEPS } from "./catalog";
import {
    acknowledgeTourSteps,
    createTourStepHashes,
    getUnacknowledgedTourSteps,
} from "./hashes";
import { TourState, TourStep } from "./types";

const step = (overrides: Partial<TourStep> = {}): TourStep => ({
    id: "welcome",
    target: { selector: '[data-tour="welcome"]' },
    titleKey: "welcome.title",
    descriptionKey: "welcome.description",
    ...overrides,
});

const translate = (key: string): string =>
    ({
        "welcome.title": "Welcome",
        "welcome.description": "See what Loom can do.",
        "welcome.changed": "See what changed in Loom.",
        "controls.continue": "Continue",
    })[key] ?? key;

const resolver = {
    exists: (key: string): boolean => translate(key) !== key,
    translate,
};

const emptyState = (): TourState => ({
    schemaVersion: 1,
    acknowledgedStepHashes: {},
});

describe("tour step hashes", () => {
    it("uses unique IDs throughout the global catalog", () => {
        const ids = GLOBAL_TOUR_STEPS.map(({ id }) => id);
        expect(new Set(ids).size).toBe(ids.length);
    });

    it("changes when canonical copy changes", async () => {
        const original = await createTourStepHashes([step()], resolver);
        const changed = await createTourStepHashes(
            [step({ descriptionKey: "welcome.changed" })],
            resolver,
        );
        const changedButton = await createTourStepHashes(
            [step({ nextButtonKey: "controls.continue" })],
            resolver,
        );

        expect(changed.welcome).not.toBe(original.welcome);
        expect(changedButton.welcome).not.toBe(original.welcome);
    });

    it("ignores non-copy configuration changes", async () => {
        const original = await createTourStepHashes([step()], resolver);
        const repositioned = await createTourStepHashes(
            [
                step({
                    align: "end",
                    side: "left",
                    waitForElementMs: 5_000,
                    target: {
                        selector: '[data-tour="moved"]',
                        viewport: "mobile",
                    },
                }),
            ],
            resolver,
        );

        expect(repositioned.welcome).toBe(original.welcome);
    });

    it("selects new hashes in catalog order", () => {
        const steps = [step(), step({ id: "second" })];
        const hashes = { welcome: "hash-2", second: "hash-new" };
        const state: TourState = {
            schemaVersion: 1,
            acknowledgedStepHashes: { welcome: ["hash-1"] },
        };

        expect(
            getUnacknowledgedTourSteps(steps, hashes, state).map(
                ({ id }) => id,
            ),
        ).toEqual(["welcome", "second"]);
    });

    it("retains hash history so acknowledged copy stays seen", () => {
        const currentStep = step();
        const state = acknowledgeTourSteps(
            {
                ...emptyState(),
                acknowledgedStepHashes: { welcome: ["old-hash"] },
            },
            [currentStep],
            { welcome: "new-hash" },
        );

        expect(state.acknowledgedStepHashes.welcome).toEqual([
            "old-hash",
            "new-hash",
        ]);
        expect(
            getUnacknowledgedTourSteps(
                [currentStep],
                { welcome: "old-hash" },
                state,
            ),
        ).toEqual([]);
    });

    it("rejects duplicate step IDs", async () => {
        await expect(
            createTourStepHashes([step(), step()], resolver),
        ).rejects.toThrow("Duplicate tour step ID: welcome");
    });

    it("rejects missing English copy", async () => {
        await expect(
            createTourStepHashes(
                [step({ descriptionKey: "welcome.missing" })],
                resolver,
            ),
        ).rejects.toThrow(
            'Missing English tour copy for step "welcome": welcome.missing',
        );
    });
});
