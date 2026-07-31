import { fireEvent, render, waitFor } from "@testing-library/react";
import { Driver, driver } from "driver.js";
import { useEffect, useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TourStep } from "./types";
import { useDriverTour } from "./useDriverTour";

const { mockFinish, mockTranslate } = vi.hoisted(() => ({
    mockFinish: vi.fn(),
    mockTranslate: vi.fn((key: string) => key),
}));

vi.mock("@mui/material", () => ({
    useMediaQuery: () => false,
}));

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: mockTranslate }),
}));

vi.mock("driver.js", () => ({
    driver: vi.fn(),
}));

const DELAYED_STEP: TourStep = {
    id: "delayed",
    target: { selector: '[data-tour="delayed"]' },
    titleKey: "delayed.title",
    descriptionKey: "delayed.description",
    waitForElementMs: 100,
};

const DelayedFullTourHarness = () => {
    const [activeStepId, setActiveStepId] = useState<string | null>(null);
    const [showTarget, setShowTarget] = useState(false);
    const { start } = useDriverTour(mockFinish, setActiveStepId);

    useEffect(() => {
        if (activeStepId !== DELAYED_STEP.id) return;
        const timeout = window.setTimeout(() => setShowTarget(true), 10);
        return () => window.clearTimeout(timeout);
    }, [activeStepId]);

    return (
        <>
            <button
                onClick={() => start({ mode: "full", steps: [DELAYED_STEP] })}
            >
                Start
            </button>
            {showTarget && <div data-tour="delayed">Delayed target</div>}
        </>
    );
};

describe("useDriverTour", () => {
    let driverInstance: Driver;

    beforeEach(() => {
        vi.clearAllMocks();
        driverInstance = {
            destroy: vi.fn(),
            drive: vi.fn(),
        } as unknown as Driver;
        vi.mocked(driver).mockReturnValue(driverInstance);
    });

    it("waits for the first target of a full tour when configured", async () => {
        const view = render(<DelayedFullTourHarness />);

        fireEvent.click(view.getByRole("button", { name: "Start" }));

        await waitFor(() =>
            expect(driverInstance.drive).toHaveBeenCalledWith(0),
        );
        expect(view.getByText("Delayed target")).toBeInTheDocument();
        expect(mockFinish).not.toHaveBeenCalled();
    });
});
