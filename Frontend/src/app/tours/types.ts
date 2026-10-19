import type { Alignment, Side } from "driver.js";

export type TourViewport = "all" | "desktop" | "mobile";

export type TourPreparation = "search-results";

/**
 * A selector the tour may point at.
 *
 * Constrained to the tour's own attributes so a step cannot come to depend on
 * a class name or an element's position. `[data-tour-anchor="true"]` is the
 * single result card the tour has settled on; scoping a step under it is what
 * keeps the card steps all describing the same result, and is required now
 * that only a window of the result list is rendered at a time.
 */
export type TourSelector =
    | `[data-tour="${string}"]`
    | '[data-tour-anchor="true"]'
    | `[data-tour-anchor="true"] [data-tour="${string}"]`;

export interface TourTarget {
    selector: TourSelector;
    viewport?: TourViewport;
}

export interface TourStep {
    id: string;
    target: TourTarget;
    titleKey: string;
    descriptionKey: string;
    doneButtonKey?: string;
    nextButtonKey?: string;
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
