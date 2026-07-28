import { describe, expect, it } from "vitest";

import { filterTourSteps } from "./responsive";
import { TourStep } from "./types";

const steps: readonly TourStep[] = [
    {
        id: "all",
        target: { selector: '[data-tour="all"]' },
        titleKey: "all.title",
        descriptionKey: "all.description",
    },
    {
        id: "desktop",
        target: { selector: '[data-tour="desktop"]', viewport: "desktop" },
        titleKey: "desktop.title",
        descriptionKey: "desktop.description",
    },
    {
        id: "mobile",
        target: { selector: '[data-tour="mobile"]', viewport: "mobile" },
        titleKey: "mobile.title",
        descriptionKey: "mobile.description",
    },
];

describe("responsive tour steps", () => {
    it("keeps shared and desktop steps on wide screens", () => {
        expect(filterTourSteps(steps, false).map(({ id }) => id)).toEqual([
            "all",
            "desktop",
        ]);
    });

    it("keeps shared and mobile steps on small screens", () => {
        expect(filterTourSteps(steps, true).map(({ id }) => id)).toEqual([
            "all",
            "mobile",
        ]);
    });
});
