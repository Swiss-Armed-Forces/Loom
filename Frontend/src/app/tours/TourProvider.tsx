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
import { useLocation } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectFiles, updateQuery } from "@app/slices/searchSlice";

import { GLOBAL_TOUR_STEPS, INCREMENTAL_TOUR_INTRO_STEP } from "./catalog";
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
    const isMobile = useMediaQuery("(max-width:600px)");
    const location = useLocation();
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
    const existingResultFileId = useMemo(
        () =>
            Object.entries(files).find(
                ([, file]) => file.meta !== null && !file.stale,
            )?.[0] ?? null,
        [files],
    );

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
        },
        [resetTourScene],
    );
    const handleStepChange = useCallback((stepId: string) => {
        setActiveTourStepId(stepId);
        setShowQueryOverview(QUERY_OVERVIEW_STEPS.has(stepId));
        if (stepId === "results-tabs") window.scrollTo({ top: 0 });
    }, []);
    const handleStepNext = useCallback(
        async (stepId: string): Promise<boolean> => {
            if (stepId !== "search-all") return true;
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
        [dispatch],
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
        [cancelPendingPreparation, dispatch, existingResultFileId],
    );

    const startConfiguredTour = useCallback(
        async (
            steps: readonly TourStep[],
            mode: TourMode,
            requestId: number,
            automatic: boolean,
        ): Promise<void> => {
            const eligibleSteps = filterTourSteps(steps, isMobile);
            if (eligibleSteps.length === 0) return;
            if (
                mode === "incremental" &&
                !(await prepareIncrementalTour(eligibleSteps))
            ) {
                return;
            }
            if (requestId !== startRequestRef.current) return;
            if (automatic && pathnameRef.current !== "/search") return;
            start({
                mode,
                steps:
                    mode === "incremental"
                        ? [INCREMENTAL_TOUR_INTRO_STEP, ...eligibleSteps]
                        : eligibleSteps,
            });
        },
        [isMobile, prepareIncrementalTour, start],
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

            start({ mode: "full", steps: GLOBAL_TOUR_STEPS });
        });
    }, [cancelPendingPreparation, loadStepHashes, start, startConfiguredTour]);

    const dismissActiveTour = useCallback(() => {
        cancelPendingPreparation();
        startRequestRef.current += 1;
        dismiss();
    }, [cancelPendingPreparation, dismiss]);

    useEffect(() => {
        if (location.pathname !== "/search") {
            cancelPendingPreparation();
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
            location.pathname !== "/search" ||
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
            automaticStartAttemptedRef.current = true;
            const requestId = ++startRequestRef.current;
            void startConfiguredTour(steps, mode, requestId, true);
        });
    }, [location.pathname, startConfiguredTour, stepHashes]);

    const contextValue: TourContextValue = {
        isTourActive: isActive,
        showQueryOverview,
        activeTourStepId,
        tourDetailFileId,
        dismissActiveTour,
        startTour,
    };

    return (
        <TourContext.Provider value={contextValue}>
            {children}
        </TourContext.Provider>
    );
};
