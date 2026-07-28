import { TourStep } from "./types";

export const filterTourSteps = (
    steps: readonly TourStep[],
    isMobile: boolean,
): readonly TourStep[] =>
    steps.filter(({ target }) => {
        const viewport = target.viewport ?? "all";
        return (
            viewport === "all" ||
            (viewport === "mobile" && isMobile) ||
            (viewport === "desktop" && !isMobile)
        );
    });
