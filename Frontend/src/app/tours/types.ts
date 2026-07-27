import type { Alignment, Side } from "driver.js";

export type TourViewport = "all" | "desktop" | "mobile";

export interface TourTarget {
    selector: `[data-tour="${string}"]`;
    viewport?: TourViewport;
}

export interface TourStep {
    id: string;
    target: TourTarget;
    titleKey: string;
    descriptionKey: string;
    side?: Side;
    align?: Alignment;
    waitForElementMs?: number;
    skipIfMissing?: boolean;
}

export type TourOutcome = "completed" | "dismissed";

export interface TourState {
    schemaVersion: 1;
    outcome?: TourOutcome;
}

export interface TourContextValue {
    isTourActive: boolean;
    dismissActiveTour: () => void;
    startTour: () => boolean;
}
