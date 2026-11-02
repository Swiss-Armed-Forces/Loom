import { useMediaQuery } from "@mui/material";
import {
    ReactNode,
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { isLoadedResult } from "@app/slices/searchFileEntry";
import { selectFiles, selectQuery, updateQuery } from "@app/slices/searchSlice";
import { SearchQuery } from "@features/common/utils/model";

import {
    GLOBAL_TOUR_STEPS,
    INCREMENTAL_TOUR_INTRO_STEP,
    TOUR_CONCLUSION_STEP,
} from "./catalog";
import {
    acknowledgeTourSteps,
    createTourStepHashes,
    getUnacknowledgedTourSteps,
    TourStepHashes,
} from "./hashes";
import { filterTourSteps } from "./responsive";
import { startWhenDialogsClose } from "./startWhenDialogsClose";
import { loadTourState, saveTourState } from "./storage";
import { TourContext } from "./TourContext";
import {
    TourContextValue,
    TourFinishResult,
    TourMode,
    TourState,
    TourStep,
} from "./types";
import { useDriverTour } from "./useDriverTour";

const isLoomPage = (pathname: string): boolean =>
    pathname === "/search" || pathname === "/archives";

interface TourProviderProps {
    children: ReactNode;
}

const QUERY_OVERVIEW_STEPS = new Set([
    "welcome",
    "global-search",
    "query-overview",
    "keyboard-shortcuts",
    "search-all",
]);

export const TourProvider = ({ children }: TourProviderProps) => {
    const dispatch = useAppDispatch();
    const files = useAppSelector(selectFiles);
    const query = useAppSelector(selectQuery);
    const isMobile = useMediaQuery("(max-width:600px)");
    const location = useLocation();
    const navigate = useNavigate();
    const {
        i18n,
        ready: englishCopyReady,
        t: translateEnglishCopy,
    } = useTranslation(undefined, { lng: "en" });
    const [showQueryOverview, setShowQueryOverview] = useState(false);
    const [activeTourStepId, setActiveTourStepId] = useState<string | null>(
        null,
    );
    const [tourDetailFileId, setTourDetailFileId] = useState<string | null>(
        null,
    );
    const [stepHashes, setStepHashes] = useState<TourStepHashes | null>(null);
    const stepHashesRef = useRef<TourStepHashes | null>(null);
    const stepHashPromiseRef = useRef<Promise<TourStepHashes | null> | null>(
        null,
    );
    const tourStateRef = useRef<TourState>(loadTourState());
    const automaticStartAttemptedRef = useRef(false);
    const startRequestRef = useRef(0);
    const pendingPreparationCancelRef = useRef<(() => void) | null>(null);
    const pathnameRef = useRef(location.pathname);
    pathnameRef.current = location.pathname;
    const queryRef = useRef(query);
    queryRef.current = query;
    // The search the user had before the tour took the search over to show
    // results of its own. Handed back when the tour ends, however it ends,
    // but only once the tour has actually run a search of its own.
    const preTourQueryRef = useRef<SearchQuery | null>(null);
    const tourDroveSearchRef = useRef(false);
    // Stale cards count as loaded results elsewhere, but the tour drives a real
    // card: a stale entry has no usable preview, so it is skipped here on
    // purpose rather than by drift from `isLoadedResult`.
    //
    // A card carrying all three optional elements is preferred, because the
    // thumbnail, tags and sub-item steps each point inside the one card the
    // tour has settled on and have nothing to point at otherwise. Finding
    // whichever card in the whole list happens to have the element could point
    // at three different cards, and is not possible at all while only a window
    // of the list is rendered.
    const existingResultFileId = useMemo(() => {
        const usable = Object.entries(files).filter(
            ([, file]) => isLoadedResult(file) && !file.stale,
        );
        const complete = usable.find(
            ([, file]) =>
                file.preview?.thumbnailFileId &&
                file.preview.tags?.length &&
                file.preview.attachments?.length,
        );
        return (complete ?? usable[0])?.[0] ?? null;
    }, [files]);

    const loadStepHashes = useCallback(async () => {
        if (englishCopyReady === false) return null;
        if (stepHashesRef.current) return stepHashesRef.current;
        if (stepHashPromiseRef.current) return stepHashPromiseRef.current;

        stepHashPromiseRef.current = createTourStepHashes(GLOBAL_TOUR_STEPS, {
            exists: (key) => i18n.exists(key, { lng: "en" }),
            translate: (key) => translateEnglishCopy(key),
        })
            .then((hashes) => {
                stepHashesRef.current = hashes;
                setStepHashes(hashes);
                return hashes;
            })
            .catch((error) => {
                console.warn("Could not fingerprint tour steps:", error);
                return null;
            })
            .finally(() => {
                stepHashPromiseRef.current = null;
            });
        return stepHashPromiseRef.current;
    }, [englishCopyReady, i18n, translateEnglishCopy]);

    useEffect(() => {
        if (englishCopyReady === false) return;
        void loadStepHashes();
    }, [englishCopyReady, loadStepHashes]);

    const resetTourScene = useCallback(() => {
        setShowQueryOverview(false);
        setActiveTourStepId(null);
        setTourDetailFileId(null);
    }, []);

    const cancelPendingPreparation = useCallback(() => {
        const cancel = pendingPreparationCancelRef.current;
        pendingPreparationCancelRef.current = null;
        cancel?.();
    }, []);

    /** Remember the search the tour is about to take over.
     *
     *  Keeps the first snapshot: once the tour has installed a query of its
     *  own, that query is not what the user was looking at. */
    const captureQueryForTour = useCallback(() => {
        if (preTourQueryRef.current) return;
        preTourQueryRef.current = queryRef.current;
    }, []);

    /** Put the search back the way the tour found it.
     *
     *  The tour drives the search itself - `search-all` and the incremental
     *  preparation both run `*` - so whatever the user was looking at is gone
     *  by the time it ends. Restoring from here rather than from the
     *  conclusion step covers a dismissal half way through as well. A tour
     *  that never reached a search of its own leaves the query alone; one that
     *  started with no query to speak of has nothing to give back and ends on
     *  the empty query the conclusion sets. */
    const restorePreTourQuery = useCallback(() => {
        const preTourQuery = preTourQueryRef.current;
        const tookOverSearch = tourDroveSearchRef.current;
        preTourQueryRef.current = null;
        tourDroveSearchRef.current = false;
        if (!tookOverSearch || !preTourQuery?.query) return;
        dispatch(
            updateQuery({
                query: preTourQuery.query,
                sortField: preTourQuery.sortField ?? null,
                sortDirection: preTourQuery.sortDirection ?? null,
            }),
        );
    }, [dispatch]);

    const persistOutcome = useCallback(
        ({ acknowledgedSteps, mode, outcome }: TourFinishResult) => {
            const hashes = stepHashesRef.current;
            if (hashes) {
                let nextState = acknowledgeTourSteps(
                    tourStateRef.current,
                    acknowledgedSteps,
                    hashes,
                );
                if (mode === "full") {
                    nextState = {
                        ...nextState,
                        introductionOutcome: outcome,
                    };
                }
                tourStateRef.current = nextState;
                saveTourState(nextState);
            }
            resetTourScene();
            restorePreTourQuery();
        },
        [resetTourScene, restorePreTourQuery],
    );
    const handleStepChange = useCallback((stepId: string) => {
        setActiveTourStepId(stepId);
        setShowQueryOverview(QUERY_OVERVIEW_STEPS.has(stepId));
        if (stepId === "results-list") window.scrollTo({ top: 0 });
    }, []);
    const handleStepNext = useCallback(
        async (stepId: string): Promise<boolean> => {
            if (stepId === "header-archives-tab") {
                navigate("/archives");
                return true;
            }
            if (stepId === "conclusion") {
                // A query the tour took over is handed back by persistOutcome
                // once the tour ends; clearing it here as well would be two
                // dispatches racing for the same state.
                if (!preTourQueryRef.current?.query) {
                    dispatch(updateQuery({ query: "", sortField: null }));
                }
                navigate("/search");
                return true;
            }
            if (stepId !== "search-all") return true;
            tourDroveSearchRef.current = true;
            try {
                const result = await dispatch(
                    updateQuery({
                        query: "*",
                        sortField: null,
                        sortDirection: "desc",
                    }),
                ).unwrap();
                setTourDetailFileId(result?.files[0]?.fileId ?? null);
                document
                    .querySelector<HTMLElement>('[data-tour="search-panel"]')
                    ?.scrollTo({ top: 0 });
                return true;
            } catch {
                return false;
            }
        },
        [dispatch, navigate],
    );
    const { dismiss, isActive, start } = useDriverTour(
        persistOutcome,
        handleStepChange,
        handleStepNext,
    );

    const prepareIncrementalTour = useCallback(
        async (steps: readonly TourStep[]): Promise<boolean> => {
            const needsSearchResults = steps.some(
                ({ preparation }) => preparation === "search-results",
            );
            const includesSearchStep = steps.some(
                ({ id }) => id === "search-all",
            );
            if (!needsSearchResults || includesSearchStep) return true;

            if (existingResultFileId) {
                setTourDetailFileId(existingResultFileId);
                return true;
            }

            cancelPendingPreparation();
            captureQueryForTour();
            tourDroveSearchRef.current = true;
            const request = dispatch(
                updateQuery({
                    query: "*",
                    sortField: null,
                    sortDirection: "desc",
                }),
            );
            let cancelled = false;
            const cancel = () => {
                cancelled = true;
                request.abort();
            };
            pendingPreparationCancelRef.current = cancel;

            try {
                const result = await request.unwrap();
                if (cancelled) return false;
                setTourDetailFileId(result?.files[0]?.fileId ?? null);
                return true;
            } catch {
                return false;
            } finally {
                if (pendingPreparationCancelRef.current === cancel) {
                    pendingPreparationCancelRef.current = null;
                }
            }
        },
        [
            cancelPendingPreparation,
            captureQueryForTour,
            dispatch,
            existingResultFileId,
        ],
    );

    const startConfiguredTour = useCallback(
        async (
            steps: readonly TourStep[],
            mode: TourMode,
            requestId: number,
            automatic: boolean,
        ): Promise<boolean> => {
            const eligibleSteps = filterTourSteps(steps, isMobile);
            if (eligibleSteps.length === 0) return true;
            // For automatic incremental tours, defer if every eligible step
            // requires a pathname that doesn't match the current one.
            if (automatic && mode === "incremental") {
                const currentPathname = pathnameRef.current;
                const hasReachableStep = eligibleSteps.some((step) => {
                    const requiredPathname =
                        step.requiresPathname ??
                        (step.preparation === "search-results"
                            ? "/search"
                            : undefined);
                    return (
                        !requiredPathname ||
                        requiredPathname === currentPathname
                    );
                });
                if (!hasReachableStep) return false;
            }
            if (
                mode === "incremental" &&
                !(await prepareIncrementalTour(eligibleSteps))
            ) {
                return false;
            }
            if (requestId !== startRequestRef.current) return true;
            if (automatic && !isLoomPage(pathnameRef.current)) return false;
            captureQueryForTour();
            start({
                mode,
                steps:
                    mode === "incremental"
                        ? [
                              INCREMENTAL_TOUR_INTRO_STEP,
                              ...eligibleSteps.filter(
                                  (s) => s.id !== "conclusion",
                              ),
                              TOUR_CONCLUSION_STEP,
                          ]
                        : eligibleSteps,
            });
            return true;
        },
        [captureQueryForTour, isMobile, prepareIncrementalTour, start],
    );

    const startTour = useCallback(() => {
        automaticStartAttemptedRef.current = true;
        cancelPendingPreparation();
        const requestId = ++startRequestRef.current;
        void loadStepHashes().then((hashes) => {
            if (requestId !== startRequestRef.current) return;
            if (hashes) {
                void startConfiguredTour(
                    GLOBAL_TOUR_STEPS,
                    "full",
                    requestId,
                    false,
                );
                return;
            }

            captureQueryForTour();
            start({ mode: "full", steps: GLOBAL_TOUR_STEPS });
        });
    }, [
        cancelPendingPreparation,
        captureQueryForTour,
        loadStepHashes,
        start,
        startConfiguredTour,
    ]);

    const dismissActiveTour = useCallback(() => {
        cancelPendingPreparation();
        startRequestRef.current += 1;
        dismiss();
    }, [cancelPendingPreparation, dismiss]);

    useEffect(() => {
        cancelPendingPreparation();
        if (!isLoomPage(location.pathname)) {
            startRequestRef.current += 1;
        }
    }, [cancelPendingPreparation, location.pathname]);

    useEffect(
        () => () => {
            cancelPendingPreparation();
            startRequestRef.current += 1;
        },
        [cancelPendingPreparation],
    );

    useEffect(() => {
        if (
            !isLoomPage(location.pathname) ||
            automaticStartAttemptedRef.current ||
            !stepHashes
        ) {
            return;
        }

        const mode: TourMode =
            tourStateRef.current.introductionOutcome === undefined
                ? "full"
                : "incremental";
        const steps =
            mode === "full"
                ? GLOBAL_TOUR_STEPS
                : getUnacknowledgedTourSteps(
                      GLOBAL_TOUR_STEPS,
                      stepHashes,
                      tourStateRef.current,
                  );
        if (steps.length === 0) {
            automaticStartAttemptedRef.current = true;
            return;
        }

        return startWhenDialogsClose(() => {
            if (automaticStartAttemptedRef.current) return;
            const requestId = ++startRequestRef.current;
            void startConfiguredTour(steps, mode, requestId, true).then(
                (attempted) => {
                    if (attempted) automaticStartAttemptedRef.current = true;
                },
            );
        });
    }, [location.pathname, startConfiguredTour, stepHashes]);

    // Memoised because a new context value re-renders every useTour() consumer —
    // ActivityBar, both sidebars, SearchResults, BurgerMenu — and context updates pass
    // straight through React.memo. The provider itself subscribes to `files`, so an
    // unmemoised value turns every preview arrival into a page-wide re-render.
    const contextValue = useMemo<TourContextValue>(
        () => ({
            isTourActive: isActive,
            showQueryOverview,
            activeTourStepId,
            tourDetailFileId,
            dismissActiveTour,
            startTour,
        }),
        [
            isActive,
            showQueryOverview,
            activeTourStepId,
            tourDetailFileId,
            dismissActiveTour,
            startTour,
        ],
    );

    return (
        <TourContext.Provider value={contextValue}>
            {children}
        </TourContext.Provider>
    );
};
