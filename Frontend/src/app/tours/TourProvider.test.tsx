import { act, fireEvent, render, waitFor } from "@testing-library/react";
import { Config, DriveStep, Driver, PopoverDOM, driver } from "driver.js";
import { ReactNode, StrictMode, useEffect, useState } from "react";
import { MemoryRouter, useNavigate } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { updateQuery } from "@app/slices/searchSlice";

import { GLOBAL_TOUR_STEPS } from "./catalog";
import { createTourStepHashes } from "./hashes";
import { TOUR_STORAGE_KEY } from "./storage";
import { TourProvider } from "./TourProvider";
import { useTour } from "./useTour";

const {
    mockCreateTourStepHashes,
    mockDispatch,
    mockFiles,
    mockIsMobile,
    mockTranslate,
} = vi.hoisted(() => ({
    mockCreateTourStepHashes: vi.fn(),
    mockDispatch: vi.fn(),
    mockFiles: { current: {} as Record<string, unknown> },
    mockIsMobile: { current: false },
    mockTranslate: vi.fn((key: string) => key),
}));

vi.mock("@app/hooks", () => ({
    useAppDispatch: () => mockDispatch,
    useAppSelector: () => mockFiles.current,
}));

vi.mock("@app/slices/searchSlice", () => ({
    selectFiles: vi.fn(),
    updateQuery: vi.fn((payload) => ({
        type: "search/updateQuery",
        payload,
    })),
}));

vi.mock("@mui/material", () => ({
    useMediaQuery: () => mockIsMobile.current,
}));

vi.mock("react-i18next", () => ({
    useTranslation: () => ({
        i18n: { exists: () => true },
        ready: true,
        t: mockTranslate,
    }),
}));

vi.mock("./hashes", async (importOriginal) => {
    const original = await importOriginal<typeof import("./hashes")>();
    return {
        ...original,
        createTourStepHashes: mockCreateTourStepHashes,
    };
});

vi.mock("driver.js", () => ({
    driver: vi.fn(),
}));

const mockedDriver = vi.mocked(driver);
let capturedConfig: Config;
let driverInstance: Driver;

const seenTourState = (outcome: "completed" | "dismissed") => ({
    schemaVersion: 1,
    introductionOutcome: outcome,
    acknowledgedStepHashes: Object.fromEntries(
        GLOBAL_TOUR_STEPS.map(({ id }) => [id, [`hash-${id}`]]),
    ),
});

const tourStateWithChangedSteps = (...stepIds: string[]) => {
    const state = seenTourState("completed");
    stepIds.forEach((stepId) => {
        state.acknowledgedStepHashes[stepId] = [`old-hash-${stepId}`];
    });
    return state;
};

const createDriverInstance = (): Driver =>
    ({
        destroy: vi.fn(),
        drive: vi.fn(),
        moveNext: vi.fn(),
        movePrevious: vi.fn(),
        moveTo: vi.fn(),
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

const deferred = <Value,>() => {
    let resolve!: (value: Value) => void;
    let reject!: (reason: unknown) => void;
    const promise = new Promise<Value>((resolvePromise, rejectPromise) => {
        resolve = resolvePromise;
        reject = rejectPromise;
    });
    return { promise, reject, resolve };
};

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

const RouteHarness = ({ children }: { children: ReactNode }) => {
    const navigate = useNavigate();
    return (
        <>
            <button onClick={() => navigate("/archives")}>Open archives</button>
            {children}
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
            <div data-tour="results-tabs">Results tabs</div>
            <div data-tour="result-card-processing-status">
                File processing status
            </div>
            <div data-tour="result-card">Result card</div>
            <div data-tour="archives-tab">Archives tab</div>
            <div data-tour="menu">Menu</div>
        </>
    );
};

const DynamicTourViewHarness = () => {
    const { activeTourStepId, isTourActive } = useTour();
    return (
        <>
            <div data-testid="dynamic-tour-view">
                {isTourActive ? "active" : "inactive"}:{activeTourStepId}
            </div>
            {activeTourStepId === "detail-highlights" && (
                <div data-tour="detail-highlights">Highlights</div>
            )}
            {activeTourStepId === "folders" && (
                <div data-tour="sidebar-folders">Folder sidebar</div>
            )}
        </>
    );
};

const DelayedTargetHarness = () => {
    const { activeTourStepId } = useTour();
    const [showTarget, setShowTarget] = useState(false);

    useEffect(() => {
        if (activeTourStepId !== "folder-tree-node") return;
        const timeout = window.setTimeout(() => setShowTarget(true), 10);
        return () => window.clearTimeout(timeout);
    }, [activeTourStepId]);

    return showTarget ? (
        <div data-tour="folder-tree-node">Delayed folder</div>
    ) : null;
};

describe("TourProvider", () => {
    beforeEach(() => {
        vi.stubEnv("DEV", false);
        vi.clearAllMocks();
        window.localStorage.clear();
        mockFiles.current = {};
        mockIsMobile.current = false;
        mockCreateTourStepHashes.mockImplementation(
            async (steps: typeof GLOBAL_TOUR_STEPS) =>
                Object.fromEntries(steps.map(({ id }) => [id, `hash-${id}`])),
        );
        mockDispatch.mockReturnValue({
            abort: vi.fn(),
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

    it("allows manual starts even after the tour was previously dismissed", async () => {
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(seenTourState("dismissed")),
        );
        const view = renderProvider(<ManualTourHarness />);

        await act(
            () => new Promise((resolve) => window.setTimeout(resolve, 20)),
        );
        expect(mockedDriver).not.toHaveBeenCalled();

        fireEvent.click(view.getByRole("button", { name: "Take a Tour" }));

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
    });

    it("introduces only the steps whose copy hash changed", async () => {
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(tourStateWithChangedSteps("header-archives-tab")),
        );

        renderProvider(<TourViewHarness />);

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        expect(capturedConfig.steps).toHaveLength(3);
        expect(capturedConfig.steps?.[0].element).toBe(
            '[data-tour="branding"]',
        );
        expect(capturedConfig.steps?.[0].popover?.title).toBe(
            "tour.steps.incrementalWelcome.title",
        );
        expect(capturedConfig.steps?.[1].element).toBe(
            '[data-tour="archives-tab"]',
        );

        await act(async () => {
            await capturedConfig.steps?.[0].popover?.onNextClick?.(
                undefined,
                capturedConfig.steps[0] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 0,
                },
            );
        });
        expect(driverInstance.moveTo).toHaveBeenCalledWith(1);

        await act(async () => {
            await capturedConfig.steps?.[1].popover?.onNextClick?.(
                undefined,
                capturedConfig.steps?.[1] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 1,
                },
            );
        });

        await act(async () => {
            await capturedConfig.steps?.[2].popover?.onDoneClick?.(
                undefined,
                capturedConfig.steps?.[2] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 2,
                },
            );
        });

        const stored = JSON.parse(
            window.localStorage.getItem(TOUR_STORAGE_KEY)!,
        );
        expect(stored.introductionOutcome).toBe("completed");
        expect(stored.acknowledgedStepHashes["header-archives-tab"]).toEqual([
            "old-hash-header-archives-tab",
            "hash-header-archives-tab",
        ]);
    });

    it("runs a final search-all action before completing", async () => {
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(tourStateWithChangedSteps("search-all")),
        );

        renderProvider(<TourViewHarness />);

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        expect(capturedConfig.steps).toHaveLength(3);
        expect(capturedConfig.steps?.[1].popover?.nextBtnText).toBe(
            "tour.controls.searchAll",
        );

        await act(async () => {
            await capturedConfig.steps?.[1].popover?.onNextClick?.(
                undefined,
                capturedConfig.steps[1] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 1,
                },
            );
        });

        expect(updateQuery).toHaveBeenCalledWith({
            query: "*",
            sortField: null,
            sortDirection: "desc",
        });

        await act(async () => {
            await capturedConfig.steps?.[2].popover?.onDoneClick?.(
                undefined,
                capturedConfig.steps[2] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 2,
                },
            );
        });

        expect(driverInstance.destroy).toHaveBeenCalledOnce();
        expect(
            JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!)
                .acknowledgedStepHashes["search-all"],
        ).toEqual(["old-hash-search-all", "hash-search-all"]);
    });

    it("keeps a final search-all step active when its action fails", async () => {
        mockDispatch.mockReturnValue({
            unwrap: vi.fn().mockRejectedValue(new Error("search failed")),
        });
        const storedState = tourStateWithChangedSteps("search-all");
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(storedState),
        );

        renderProvider(<TourViewHarness />);

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        await act(async () => {
            await capturedConfig.steps?.[1].popover?.onNextClick?.(
                undefined,
                capturedConfig.steps[1] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 1,
                },
            );
        });

        expect(driverInstance.destroy).not.toHaveBeenCalled();
        expect(
            JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!),
        ).toEqual(storedState);
    });

    it("renders a dynamic sidebar target before validating the tour", async () => {
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(tourStateWithChangedSteps("folders")),
        );

        const view = renderProvider(<DynamicTourViewHarness />);

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        expect(capturedConfig.steps).toHaveLength(3);
        expect(capturedConfig.steps?.[1].element).toBe(
            '[data-tour="sidebar-folders"]',
        );
        expect(view.getByTestId("dynamic-tour-view")).toHaveTextContent(
            "active:folders",
        );
        expect(view.getByText("Folder sidebar")).toBeInTheDocument();
    });

    it("waits for an asynchronous target before starting", async () => {
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(tourStateWithChangedSteps("folder-tree-node")),
        );

        const view = renderProvider(<DelayedTargetHarness />);

        await waitFor(() =>
            expect(driverInstance.drive).toHaveBeenCalledWith(1),
        );
        expect(view.getByText("Delayed folder")).toBeInTheDocument();
    });

    it("moves between dynamically rendered document and sidebar steps", async () => {
        let targetWhenMovingNext: Element | null = null;
        let targetWhenMovingPrevious: Element | null = null;
        vi.mocked(driverInstance.moveTo).mockImplementation((index) => {
            if (index === 2) {
                targetWhenMovingNext = document.querySelector(
                    '[data-tour="sidebar-folders"]',
                );
            } else if (index === 1) {
                targetWhenMovingPrevious = document.querySelector(
                    '[data-tour="detail-highlights"]',
                );
            }
        });
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(
                tourStateWithChangedSteps("detail-highlights", "folders"),
            ),
        );

        const view = renderProvider(<DynamicTourViewHarness />);

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        expect(updateQuery).toHaveBeenCalledWith({
            query: "*",
            sortField: null,
            sortDirection: "desc",
        });
        expect(capturedConfig.steps).toHaveLength(4);
        expect(capturedConfig.steps?.map(({ element }) => element)).toEqual([
            '[data-tour="branding"]',
            '[data-tour="detail-highlights"]',
            '[data-tour="sidebar-folders"]',
            '[data-tour="branding"]',
        ]);
        expect(capturedConfig.skipMissingElement).toBe(false);
        expect(
            capturedConfig.steps?.map(({ skipMissingElement }) =>
                Boolean(skipMissingElement),
            ),
        ).toEqual([false, false, false, false]);
        expect(view.getByTestId("dynamic-tour-view")).toHaveTextContent(
            "active:detail-highlights",
        );

        await act(async () => {
            await capturedConfig.steps?.[1].popover?.onNextClick?.(
                undefined,
                capturedConfig.steps?.[1] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 1,
                },
            );
        });

        expect(driverInstance.moveTo).toHaveBeenCalledWith(2);
        expect(targetWhenMovingNext).not.toBeNull();
        expect(view.getByTestId("dynamic-tour-view")).toHaveTextContent(
            "active:folders",
        );
        expect(view.getByText("Folder sidebar")).toBeInTheDocument();

        await act(async () => {
            await capturedConfig.steps?.[2].popover?.onPrevClick?.(
                undefined,
                capturedConfig.steps?.[2] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 2,
                },
            );
        });

        expect(driverInstance.moveTo).toHaveBeenCalledWith(1);
        expect(targetWhenMovingPrevious).not.toBeNull();
        expect(view.getByTestId("dynamic-tour-view")).toHaveTextContent(
            "active:detail-highlights",
        );
        expect(view.getByText("Highlights")).toBeInTheDocument();
    });

    it("advances with Driver.js when the next target starts absent", async () => {
        const { driver: actualDriver } =
            await vi.importActual<typeof import("driver.js")>("driver.js");
        mockedDriver.mockImplementation((config = {}) => {
            capturedConfig = config;
            driverInstance = actualDriver({ ...config, animate: false });
            return driverInstance;
        });
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(
                tourStateWithChangedSteps("detail-highlights", "folders"),
            ),
        );

        const view = renderProvider(<DynamicTourViewHarness />);

        await waitFor(() => expect(driverInstance.getActiveIndex()).toBe(1));
        expect(
            document.querySelector('[data-tour="sidebar-folders"]'),
        ).toBeNull();

        fireEvent.click(
            document.querySelector<HTMLButtonElement>(
                ".driver-popover-next-btn",
            )!,
        );

        await waitFor(() => expect(driverInstance.getActiveIndex()).toBe(2));
        expect(view.getByText("Folder sidebar")).toBeInTheDocument();
        expect(view.getByTestId("dynamic-tour-view")).toHaveTextContent(
            "active:folders",
        );

        act(() => driverInstance.destroy());
    });

    it("skips an absent optional target before a dynamic target", async () => {
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(tourStateWithChangedSteps("upload", "folders")),
        );

        const view = renderProvider(<DynamicTourViewHarness />);

        await waitFor(() =>
            expect(driverInstance.drive).toHaveBeenCalledWith(2),
        );
        expect(capturedConfig.steps).toHaveLength(4);
        expect(capturedConfig.steps?.[1].element).toBe('[data-tour="upload"]');
        expect(view.getByText("Folder sidebar")).toBeInTheDocument();
        expect(view.getByTestId("dynamic-tour-view")).toHaveTextContent(
            "active:folders",
        );
    });

    it("silently prepares search results for a changed dependent step", async () => {
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(tourStateWithChangedSteps("result-card")),
        );

        const view = renderProvider(<TourViewHarness />);

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        expect(updateQuery).toHaveBeenCalledWith({
            query: "*",
            sortField: null,
            sortDirection: "desc",
        });
        expect(capturedConfig.steps).toHaveLength(3);
        expect(capturedConfig.steps?.[1].element).toBe(
            '[data-tour="result-card"]',
        );

        await act(async () => {
            await capturedConfig.steps?.[0].popover?.onNextClick?.(
                undefined,
                capturedConfig.steps[0] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 0,
                },
            );
        });
        expect(view.getByTestId("tour-view")).toHaveTextContent(
            "results:result-card:file-1",
        );
    });

    it("reuses existing results when preparing an incremental tour", async () => {
        mockFiles.current = {
            "existing-file": { meta: {}, stale: false },
        };
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(tourStateWithChangedSteps("result-card")),
        );

        const view = renderProvider(<TourViewHarness />);

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        expect(mockDispatch).not.toHaveBeenCalled();
        await act(async () => {
            await capturedConfig.steps?.[0].popover?.onNextClick?.(
                undefined,
                capturedConfig.steps[0] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: 0,
                },
            );
        });
        expect(view.getByTestId("tour-view")).toHaveTextContent(
            "results:result-card:existing-file",
        );
    });

    it("leaves a changed step unacknowledged when preparation fails", async () => {
        mockDispatch.mockReturnValue({
            unwrap: vi.fn().mockRejectedValue(new Error("search failed")),
        });
        const storedState = tourStateWithChangedSteps("result-card");
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(storedState),
        );

        renderProvider(<TourViewHarness />);

        await waitFor(() => expect(mockDispatch).toHaveBeenCalled());
        expect(mockedDriver).not.toHaveBeenCalled();
        expect(
            JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!),
        ).toEqual(storedState);
    });

    it("does not start after leaving search during preparation", async () => {
        const searchResult = deferred<{ files: { fileId: string }[] }>();
        const abort = vi.fn();
        mockDispatch.mockReturnValue({
            abort,
            unwrap: () => searchResult.promise,
        });
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(tourStateWithChangedSteps("result-card")),
        );
        const view = renderProvider(
            <RouteHarness>
                <TourViewHarness />
            </RouteHarness>,
        );

        await waitFor(() => expect(mockDispatch).toHaveBeenCalled());
        fireEvent.click(view.getByRole("button", { name: "Open archives" }));
        await act(async () =>
            searchResult.resolve({ files: [{ fileId: "file-1" }] }),
        );

        expect(abort).toHaveBeenCalledOnce();
        expect(mockedDriver).not.toHaveBeenCalled();
    });

    it("does not let late automatic preparation replace a manual tour", async () => {
        const searchResult = deferred<{ files: { fileId: string }[] }>();
        const abort = vi.fn();
        mockDispatch.mockReturnValue({
            abort,
            unwrap: () => searchResult.promise,
        });
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(tourStateWithChangedSteps("result-card")),
        );
        const view = renderProvider(<ManualTourHarness />);

        await waitFor(() => expect(mockDispatch).toHaveBeenCalled());
        fireEvent.click(view.getByRole("button", { name: "Take a Tour" }));
        await waitFor(() => expect(mockedDriver).toHaveBeenCalledTimes(1));

        await act(async () =>
            searchResult.resolve({ files: [{ fileId: "file-1" }] }),
        );
        expect(abort).toHaveBeenCalledOnce();
        expect(mockedDriver).toHaveBeenCalledTimes(1);
        expect(capturedConfig.steps).toHaveLength(GLOBAL_TOUR_STEPS.length);
    });

    it("starts a manual tour when copy hashing is unavailable", async () => {
        vi.mocked(createTourStepHashes).mockRejectedValue(
            new Error("hashing unavailable"),
        );
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(seenTourState("completed")),
        );
        const view = renderProvider(<ManualTourHarness />);

        fireEvent.click(view.getByRole("button", { name: "Take a Tour" }));

        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());
        expect(window.localStorage.getItem(TOUR_STORAGE_KEY)).toBe(
            JSON.stringify(seenTourState("completed")),
        );
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
        expect(driverInstance.moveTo).toHaveBeenCalledWith(5);
        expect(view.getByTestId("tour-view")).toHaveTextContent(
            "results:results-tabs:file-1",
        );
        expect(window.localStorage.getItem(TOUR_STORAGE_KEY)).toBeNull();

        const finalIndex = capturedConfig.steps!.length - 1;
        await act(async () => {
            await capturedConfig.steps?.[finalIndex].popover?.onDoneClick?.(
                undefined,
                capturedConfig.steps?.[finalIndex] as DriveStep,
                {
                    config: capturedConfig,
                    state: {},
                    driver: driverInstance,
                    index: finalIndex,
                },
            );
        });

        expect(
            JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!),
        ).toMatchObject({
            schemaVersion: 1,
            introductionOutcome: "completed",
        });
        expect(
            JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!)
                .acknowledgedStepHashes.welcome,
        ).toEqual(["hash-welcome"]);
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

        expect(driverInstance.moveTo).not.toHaveBeenCalled();
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

        await act(async () => {
            await capturedConfig.steps?.[5].popover?.onPrevClick?.(
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

        expect(driverInstance.moveTo).toHaveBeenCalledWith(4);
        expect(view.getByTestId("tour-view")).toHaveTextContent("overview");
    });

    it("offers a skip button on non-last steps that jumps to the conclusion", async () => {
        renderProvider(<div data-tour="branding">Loom</div>);
        await waitFor(() => expect(driverInstance.drive).toHaveBeenCalled());

        const totalSteps = capturedConfig.steps!.length;

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

        expect(driverInstance.moveTo).toHaveBeenCalledWith(totalSteps - 1);
        expect(driverInstance.destroy).not.toHaveBeenCalled();

        const lastPopover = createPopover();
        act(() => {
            capturedConfig.onPopoverRender?.(lastPopover, {
                config: capturedConfig,
                state: {},
                driver: driverInstance,
                index: totalSteps - 1,
            });
        });
        expect(
            lastPopover.footerButtons.querySelector(".loom-tour-skip-btn"),
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
        ).toMatchObject({ introductionOutcome: "dismissed" });
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
        ).toMatchObject({ introductionOutcome: "dismissed" });
    });

    it("does not acknowledge a required target that is missing", async () => {
        const navigationStep = GLOBAL_TOUR_STEPS.find(
            ({ id }) => id === "header-archives-tab",
        )!;
        const originalSkipIfMissing = navigationStep.skipIfMissing;
        navigationStep.skipIfMissing = false;
        const warn = vi
            .spyOn(console, "warn")
            .mockImplementation(() => undefined);
        const storedState = tourStateWithChangedSteps("header-archives-tab");
        window.localStorage.setItem(
            TOUR_STORAGE_KEY,
            JSON.stringify(storedState),
        );

        try {
            renderProvider(<div>No archives-tab target</div>);

            await waitFor(() =>
                expect(warn).toHaveBeenCalledWith(
                    expect.stringContaining("header-archives-tab"),
                ),
            );
            expect(
                JSON.parse(window.localStorage.getItem(TOUR_STORAGE_KEY)!)
                    .acknowledgedStepHashes["header-archives-tab"],
            ).toEqual(["old-hash-header-archives-tab"]);
            expect(mockedDriver).not.toHaveBeenCalled();
        } finally {
            navigationStep.skipIfMissing = originalSkipIfMissing;
        }
    });

    it.each(["completed", "dismissed"] as const)(
        "does not restart after the tour was %s",
        async (outcome) => {
            window.localStorage.setItem(
                TOUR_STORAGE_KEY,
                JSON.stringify(seenTourState(outcome)),
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
