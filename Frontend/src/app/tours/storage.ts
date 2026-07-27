import { TourState } from "./types";

export const TOUR_STORAGE_KEY = "loom.tours.v1";

const EMPTY_TOUR_STATE: TourState = { schemaVersion: 1 };

const isTourState = (value: unknown): value is TourState => {
    if (!value || typeof value !== "object") return false;

    const candidate = value as Partial<TourState>;
    if (candidate.schemaVersion !== 1) return false;
    return (
        candidate.outcome === undefined ||
        candidate.outcome === "completed" ||
        candidate.outcome === "dismissed"
    );
};

export const loadTourState = (): TourState => {
    try {
        const stored = window.localStorage.getItem(TOUR_STORAGE_KEY);
        if (!stored) return EMPTY_TOUR_STATE;

        const parsed: unknown = JSON.parse(stored);
        return isTourState(parsed) ? parsed : EMPTY_TOUR_STATE;
    } catch {
        return EMPTY_TOUR_STATE;
    }
};

export const saveTourState = (state: TourState): void => {
    try {
        window.localStorage.setItem(TOUR_STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
        console.warn("Could not persist tour state:", error);
    }
};
