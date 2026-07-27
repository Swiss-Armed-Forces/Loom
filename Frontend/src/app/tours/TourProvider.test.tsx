import { act, fireEvent, render, waitFor } from "@testing-library/react";
import { Config, DriveStep, Driver, driver } from "driver.js";
import { ReactNode, StrictMode, useState } from "react";
import { MemoryRouter, useNavigate } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TOUR_STORAGE_KEY } from "./storage";
import { TourProvider } from "./TourProvider";

vi.mock("@mui/material", () => ({
    useMediaQuery: () => false,
}));

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("driver.js", () => ({
    driver: vi.fn(),
}));

const mockedDriver = vi.mocked(driver);
let capturedConfig: Config;
let driverInstance: Driver;

const createDriverInstance = (): Driver =>
    ({
        destroy: vi.fn(),
        drive: vi.fn(),
    }) as unknown as Driver;

const renderProvider = (children: ReactNode, strict = false) =>
    render(
        <MemoryRouter initialEntries={["/search"]}>
            {strict ? (
                <StrictMode>
                    <TourProvider>{children}</TourProvider>
                </StrictMode>
            ) : (
                <TourProvider>{children}</TourProvider>
            )}
        </MemoryRouter>,
    );

const DialogHarness = () => {
    const [open, setOpen] = useState(true);
    return (
        <>
            {open && <div role="dialog">Introduction</div>}
            <button onClick={() => setOpen(false)}>Close introduction</button>
            <div data-tour="branding">Loom</div>
        </>
    );
};

const NavigationDialogHarness = () => {
    const navigate = useNavigate();
    const [open, setOpen] = useState(true);
    return (
        <>
            {open && <div role="dialog">Introduction</div>}
            <button onClick={() => navigate("/archives")}>Open archives</button>
            <button onClick={() => navigate("/search")}>Open search</button>
            <button onClick={() => setOpen(false)}>Close introduction</button>
            <div data-tour="branding">Loom</div>
        </>
    );
};

describe("TourProvider", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        window.localStorage.clear();
        driverInstance = createDriverInstance();
        mockedDriver.mockImplementation((config = {}) => {
            capturedConfig = config;
            return driverInstance;
        });
    });

    it("starts the tour and persists completion", async () => {
        renderProvider(<div data-tour="branding">Loom</div>);

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        expect(capturedConfig.steps).toHaveLength(6);

        act(() => {
            capturedConfig.onDoneClick?.(
                document.querySelector('[data-tour="branding"]') ?? undefined,
                capturedConfig.steps?.[0] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 0,
                },
            );
        });

        expect(
            JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!),
        ).toEqual({
            schemaVersion: 1,
            outcome: "completed",
        });
        expect(driverInstance.destroy).toHaveBeenCalled();
    });

    it("persists dismissal when the tour is closed", async () => {
        renderProvider(<div data-tour="branding">Loom</div>);
        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());

        act(() => {
            capturedConfig.onCloseClick?.(
                undefined,
                capturedConfig.steps?.[0] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 0,
                },
            );
        });

        expect(
            JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!),
        ).toMatchObject({ outcome: "dismissed" });
    });

    it("dismisses cleanly when no target exists", async () => {
        renderProvider(<div>No tour targets</div>);

        await waitFor(() =>
            expect(
                window.localStorage.getItem(TOUR_STORAGE_KEY),
            ).not.toBeNull(),
        );
        expect(mockedDriver).not.toHaveBeenCalled();
        expect(
            JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!),
        ).toMatchObject({ outcome: "dismissed" });
    });

    it.each(["completed", "dismissed"] as const)(
        "does not restart after the tour was %s",
        async (outcome) => {
            window.localStorage.setItem(
                TOUR_STORAGE_KEY,
                JSON.stringify({ schemaVersion: 1, outcome }),
            );

            renderProvider(<div data-tour="branding">Loom</div>);

            await act(
                () => new Promise((resolve) => window.setTimeout(resolve, 20)),
            );
            expect(mockedDriver).not.toHaveBeenCalled();
        },
    );

    it("starts only once when React Strict Mode repeats effects", async () => {
        renderProvider(<div data-tour="branding">Loom</div>, true);

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        expect(mockedDriver).toHaveBeenCalledTimes(1);
    });

    it("waits for an existing dialog to close", async () => {
        const view = renderProvider(<DialogHarness />);

        expect(mockedDriver).not.toHaveBeenCalled();

        fireEvent.click(
            view.getByRole("button", { name: "Close introduction" }),
        );
        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled(), {
            timeout: 1_000,
        });
    });

    it("reschedules a pending tour after leaving and returning", async () => {
        const view = renderProvider(<NavigationDialogHarness />);

        fireEvent.click(view.getByRole("button", { name: "Open archives" }));
        fireEvent.click(view.getByRole("button", { name: "Open search" }));
        fireEvent.click(
            view.getByRole("button", { name: "Close introduction" }),
        );

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled(), {
            timeout: 1_000,
        });
        expect(mockedDriver).toHaveBeenCalledTimes(1);
    });
});
