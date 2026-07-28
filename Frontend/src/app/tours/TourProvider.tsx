import { ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";

import { useAppDispatch } from "@app/hooks";
import { updateQuery } from "@app/slices/searchSlice";

import { GLOBAL_TOUR_STEPS } from "./catalog";
import { startWhenDialogsClose } from "./startWhenDialogsClose";
import { loadTourState, saveTourState } from "./storage";
import { TourContext } from "./TourContext";
import { TourContextValue, TourOutcome } from "./types";
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
    const location = useLocation();
    const [showQueryOverview, setShowQueryOverview] = useState(false);
    const [activeTourStepId, setActiveTourStepId] = useState<string | null>(
        null,
    );
    const [tourDetailFileId, setTourDetailFileId] = useState<string | null>(
        null,
    );
    const hasSeenTourRef = useRef(loadTourState().outcome !== undefined);
    const automaticStartAttemptedRef = useRef(false);

    const persistOutcome = useCallback((outcome: TourOutcome) => {
        hasSeenTourRef.current = true;
        setShowQueryOverview(false);
        setActiveTourStepId(null);
        setTourDetailFileId(null);
        saveTourState({ schemaVersion: 1, outcome });
    }, []);
    const handleStepChange = useCallback((stepId: string) => {
        setActiveTourStepId(stepId);
        setShowQueryOverview(QUERY_OVERVIEW_STEPS.has(stepId));
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
                return true;
            } catch {
                return false;
            }
        },
        [dispatch],
    );
    const { dismiss, isActive, start } = useDriverTour(
        GLOBAL_TOUR_STEPS,
        persistOutcome,
        handleStepChange,
        handleStepNext,
    );

    useEffect(() => {
        if (
            import.meta.env.DEV ||
            location.pathname !== "/search" ||
            hasSeenTourRef.current ||
            automaticStartAttemptedRef.current
        ) {
            return;
        }

        return startWhenDialogsClose(() => {
            automaticStartAttemptedRef.current = true;
            start();
        });
    }, [location.pathname, start]);

    const contextValue: TourContextValue = {
        isTourActive: isActive,
        showQueryOverview,
        activeTourStepId,
        tourDetailFileId,
        dismissActiveTour: dismiss,
        startTour: start,
    };

    return (
        <TourContext.Provider value={contextValue}>
            {children}
        </TourContext.Provider>
    );
};
