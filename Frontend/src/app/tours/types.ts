import type { Alignment, Side } from "driver.js";

export type TourViewport = "all" | "desktop" | "mobile";

export type TourPreparation = "search-results";

export interface TourTarget {
    selector: `[data-tour="${string}"]`;
    viewport?: TourViewport;
}

export interface TourStep {
    id: string;
    target: TourTarget;
    titleKey: string;
    descriptionKey: string;
    doneButtonKey?: string;
    nextButtonKey?: string;
    showSkipButton?: boolean;
    side?: Side;
    align?: Alignment;
    waitForElementMs?: number;
    skipIfMissing?: boolean;
    preparation?: TourPreparation;
    requiresPathname?: string;
}

export type TourOutcome = "completed" | "dismissed";

export type TourMode = "full" | "incremental";

export type TourEndReason =
    | "completed"
    | "user-dismissed"
    | "no-available-targets"
    | "required-target-missing";

export interface TourStartRequest {
    mode: TourMode;
    steps: readonly TourStep[];
}

export interface TourFinishResult {
    acknowledgedSteps: readonly TourStep[];
    mode: TourMode;
    outcome: TourOutcome;
    reason: TourEndReason;
}

export interface TourState {
    schemaVersion: 1;
    introductionOutcome?: TourOutcome;
    acknowledgedStepHashes: Record<string, string[]>;
}

export interface TourContextValue {
    isTourActive: boolean;
    showQueryOverview: boolean;
    activeTourStepId: string | null;
    tourDetailFileId: string | null;
    dismissActiveTour: () => void;
    startTour: () => void;
}
