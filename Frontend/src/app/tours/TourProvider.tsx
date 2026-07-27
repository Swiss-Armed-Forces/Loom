import { ReactNode, useCallback, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";

import { GLOBAL_TOUR_STEPS } from "./catalog";
import { startWhenDialogsClose } from "./startWhenDialogsClose";
import { loadTourState, saveTourState } from "./storage";
import { TourContext } from "./TourContext";
import { TourContextValue, TourOutcome } from "./types";
import { useDriverTour } from "./useDriverTour";

interface TourProviderProps {
    children: ReactNode;
}

export const TourProvider = ({ children }: TourProviderProps) => {
    const location = useLocation();
    const hasSeenTourRef = useRef(loadTourState().outcome !== undefined);
    const automaticStartAttemptedRef = useRef(false);

    const persistOutcome = useCallback((outcome: TourOutcome) => {
        hasSeenTourRef.current = true;
        saveTourState({ schemaVersion: 1, outcome });
    }, []);
    const { dismiss, isActive, start } = useDriverTour(
        GLOBAL_TOUR_STEPS,
        persistOutcome,
    );

    useEffect(() => {
        if (
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
        dismissActiveTour: dismiss,
        startTour: start,
    };

    return (
        <TourContext.Provider value={contextValue}>
            {children}
        </TourContext.Provider>
    );
};
