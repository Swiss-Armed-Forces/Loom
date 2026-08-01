import { TourOutcome, TourState } from "./types";

export const TOUR_STORAGE_KEY = "loom.tours.v1";

export const emptyTourState = (): TourState => ({
    schemaVersion: 1,
    acknowledgedStepHashes: {},
});

const isAcknowledgedStepHashes = (
    value: unknown,
): value is Record<string, string[]> => {
    if (!value || typeof value !== "object" || Array.isArray(value))
        return false;
    return Object.values(value).every(
        (hashes) =>
            Array.isArray(hashes) &&
            hashes.every((hash) => typeof hash === "string"),
    );
};

const isTourOutcome = (value: unknown): value is TourOutcome =>
    value === "completed" || value === "dismissed";

const isTourState = (value: unknown): value is TourState => {
    if (!value || typeof value !== "object") return false;

    const candidate = value as Partial<TourState>;
    if (candidate.schemaVersion !== 1) return false;
    if (
        candidate.introductionOutcome !== undefined &&
        !isTourOutcome(candidate.introductionOutcome)
    ) {
        return false;
    }
    return isAcknowledgedStepHashes(candidate.acknowledgedStepHashes);
};

const parseStoredValue = (): unknown => {
    const stored = window.localStorage.getItem(TOUR_STORAGE_KEY);
    if (!stored) return undefined;
    try {
        return JSON.parse(stored);
    } catch {
        return undefined;
    }
};

export const loadTourState = (): TourState => {
    try {
        const storedState = parseStoredValue();
        return isTourState(storedState) ? storedState : emptyTourState();
    } catch {
        return emptyTourState();
    }
};

export const saveTourState = (state: TourState): void => {
    try {
        window.localStorage.setItem(TOUR_STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
        console.warn("Could not persist tour state:", error);
    }
};
