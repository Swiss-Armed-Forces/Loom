import { act, fireEvent, render, waitFor } from "@testing-library/react";
import { Config, DriveStep, Driver, PopoverDOM, driver } from "driver.js";
import { ReactNode, StrictMode, useState } from "react";
import { MemoryRouter, useNavigate } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { updateQuery } from "@app/slices/searchSlice";

import { TOUR_STORAGE_KEY } from "./storage";
import { TourProvider } from "./TourProvider";
import { useTour } from "./useTour";

const { mockDispatch } = vi.hoisted(() => ({
    mockDispatch: vi.fn(),
}));

vi.mock("@app/hooks", () => ({
    useAppDispatch: () => mockDispatch,
}));

vi.mock("@app/slices/searchSlice", () => ({
    updateQuery: vi.fn((payload) => ({
        type: "search/updateQuery",
        payload,
    })),
}));

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
        moveNext: vi.fn(),
        movePrevious: vi.fn(),
    }) as unknown as Driver;

const createPopover = (): PopoverDOM => ({
    wrapper: document.createElement("div"),
    arrow: document.createElement("div"),
    title: document.createElement("header"),
    description: document.createElement("div"),
    footer: document.createElement("footer"),
    progress: document.createElement("span"),
    previousButton: document.createElement("button"),
    nextButton: document.createElement("button"),
    closeButton: document.createElement("button"),
    footerButtons: document.createElement("div"),
});

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

const ManualTourHarness = () => {
    const { startTour } = useTour();
    return (
        <>
            <button onClick={startTour}>Take a Tour</button>
            <div data-tour="branding">Loom</div>
        </>
    );
};

const TourViewHarness = () => {
    const { activeTourStepId, showQueryOverview, tourDetailFileId } = useTour();
    return (
        <>
            <div data-testid="tour-view">
                {showQueryOverview ? "overview" : "results"}:{activeTourStepId}:
                {tourDetailFileId ?? "none"}
            </div>
            <div data-tour="branding">Loom</div>
            <div data-tour="search-workspace">
                {showQueryOverview && (
                    <>
                        <div data-tour="query-overview">Queries</div>
                        <div data-tour="keyboard-shortcuts">Shortcuts</div>
                        <div data-tour="search-all-query">Search all</div>
                    </>
                )}
            </div>
            <div data-tour="processing-status">Processing status</div>
            <div data-tour="result-card-processing-status">
                File processing status
            </div>
            <div data-tour="navigation">Navigation</div>
            <div data-tour="menu">Menu</div>
        </>
    );
};

describe("TourProvider", () => {
    beforeEach(() => {
        vi.stubEnv("DEV", false);
        vi.clearAllMocks();
        window.localStorage.clear();
        mockDispatch.mockReturnValue({
            unwrap: vi.fn().mockResolvedValue({
                files: [{ fileId: "file-1" }],
            }),
        });
        driverInstance = createDriverInstance();
        mockedDriver.mockImplementation((config = {}) => {
            capturedConfig = config;
            return driverInstance;
        });
    });

    it("suppresses automatic starts in development but allows manual starts", async () => {
        vi.stubEnv("DEV", true);
        const view = renderProvider(<ManualTourHarness />);

        await act(
            () => new Promise((resolve) => window.setTimeout(resolve, 20)),
        );
        expect(mockedDriver).not.toHaveBeenCalled();
        expect(window.localStorage.getItem(TOUR_STORAGE_KEY)).toBeNull();

        fireEvent.click(view.getByRole("button", { name: "Take a Tour" }));

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
    });

    it("runs search-all before showing results and completing", async () => {
        const view = renderProvider(<TourViewHarness />);

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        expect(capturedConfig.steps?.[1].element).toBe(
            '[data-tour="global-search"]',
        );
        expect(capturedConfig.steps?.[2].element).toBe(
            '[data-tour="query-overview"]',
        );
        expect(capturedConfig.steps?.[3].element).toBe(
            '[data-tour="keyboard-shortcuts"]',
        );
        expect(capturedConfig.steps?.[4].element).toBe(
            '[data-tour="search-all-query"]',
        );
        expect(capturedConfig.steps?.[4].popover?.nextBtnText).toBe(
            "tour.controls.searchAll",
        );
        expect(capturedConfig.steps?.[5].element).toBe(
            '[data-tour="results-tabs"]',
        );
        expect(capturedConfig.steps?.[6].element).toBe(
            '[data-tour="result-card"]',
        );
        expect(capturedConfig.steps?.[8].element).toBe(
            '[data-tour="result-card-processing-status"]',
        );
        expect(view.getByTestId("tour-view")).toHaveTextContent("overview");

        await act(async () => {
            await capturedConfig.steps?.[4].popover?.onNextClick?.(
                undefined,
                capturedConfig.steps?.[4] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 4,
                },
            );
        });

        expect(updateQuery).toHaveBeenCalledWith({
            query: "*",
            sortField: null,
            sortDirection: "desc",
        });
        expect(mockDispatch).toHaveBeenCalledWith({
            type: "search/updateQuery",
            payload: {
                query: "*",
                sortField: null,
                sortDirection: "desc",
            },
        });
        expect(driverInstance.moveNext).toHaveBeenCalledOnce();
        expect(view.getByTestId("tour-view")).toHaveTextContent(
            "results:results-tabs:file-1",
        );
        expect(window.localStorage.getItem(TOUR_STORAGE_KEY)).toBeNull();

        act(() => {
            capturedConfig.onDoneClick?.(
                undefined,
                capturedConfig.steps?.[34] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 34,
                },
            );
        });

        expect(
            JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!),
        ).toEqual({ schemaVersion: 1, outcome: "completed" });
        expect(driverInstance.destroy).toHaveBeenCalled();
    });

    it("stays on search-all when the query fails", async () => {
        mockDispatch.mockReturnValue({
            unwrap: vi.fn().mockRejectedValue(new Error("search failed")),
        });
        const view = renderProvider(<TourViewHarness />);
        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());

        await act(async () => {
            await capturedConfig.steps?.[4].popover?.onNextClick?.(
                undefined,
                capturedConfig.steps?.[4] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 4,
                },
            );
        });

        expect(driverInstance.moveNext).not.toHaveBeenCalled();
        expect(view.getByTestId("tour-view")).toHaveTextContent("overview");
        expect(window.localStorage.getItem(TOUR_STORAGE_KEY)).toBeNull();
    });

    it("restores the overview when moving back from results", async () => {
        const view = renderProvider(<TourViewHarness />);
        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        await act(async () => {
            await capturedConfig.steps?.[4].popover?.onNextClick?.(
                undefined,
                capturedConfig.steps?.[4] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 4,
                },
            );
        });

        act(() => {
            capturedConfig.steps?.[5].popover?.onPrevClick?.(
                undefined,
                capturedConfig.steps?.[5] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 5,
                },
            );
        });

        expect(driverInstance.movePrevious).toHaveBeenCalledOnce();
        expect(view.getByTestId("tour-view")).toHaveTextContent("overview");
    });

    it("offers a skip action only on the welcome step", async () => {
        renderProvider(<div data-tour="branding">Loom</div>);
        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());

        const welcomePopover = createPopover();
        act(() => {
            capturedConfig.onPopoverRender?.(welcomePopover, {
                config: capturedConfig,
                state: {},
                driver: driverInstance,
                index: 0,
            });
        });

        const skipButton = welcomePopover.footerButtons.querySelector(
            ".loom-tour-skip-btn",
        );
        expect(skipButton).toHaveTextContent("tour.controls.skip");

        fireEvent.click(skipButton!);

        expect(
            JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!),
        ).toMatchObject({ outcome: "dismissed" });
        expect(driverInstance.destroy).toHaveBeenCalledTimes(1);
        expect(mockDispatch).not.toHaveBeenCalled();

        const overviewPopover = createPopover();
        act(() => {
            capturedConfig.onPopoverRender?.(overviewPopover, {
                config: capturedConfig,
                state: {},
                driver: driverInstance,
                index: 1,
            });
        });
        expect(
            overviewPopover.footerButtons.querySelector(".loom-tour-skip-btn"),
        ).toBeNull();
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
        expect(mockDispatch).not.toHaveBeenCalled();
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
