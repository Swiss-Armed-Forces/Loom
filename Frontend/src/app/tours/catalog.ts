import { TourStep } from "./types";

export const TOUR_TARGETS = {
    branding: '[data-tour="branding"]',
    globalSearch: '[data-tour="global-search"]',
    menu: '[data-tour="menu"]',
    navigation: '[data-tour="navigation"]',
    searchTools: '[data-tour="search-tools"]',
    searchWorkspace: '[data-tour="search-workspace"]',
} as const;

export const GLOBAL_TOUR_STEPS: readonly TourStep[] = [
    {
        id: "welcome",
        target: { selector: TOUR_TARGETS.branding },
        titleKey: "tour.steps.welcome.title",
        descriptionKey: "tour.steps.welcome.description",
        side: "bottom",
        align: "start",
    },
    {
        id: "search",
        target: { selector: TOUR_TARGETS.globalSearch },
        titleKey: "tour.steps.search.title",
        descriptionKey: "tour.steps.search.description",
        side: "bottom",
        align: "center",
    },
    {
        id: "workspace",
        target: { selector: TOUR_TARGETS.searchWorkspace },
        titleKey: "tour.steps.workspace.title",
        descriptionKey: "tour.steps.workspace.description",
        side: "top",
        align: "center",
    },
    {
        id: "tools",
        target: { selector: TOUR_TARGETS.searchTools },
        titleKey: "tour.steps.tools.title",
        descriptionKey: "tour.steps.tools.description",
        side: "right",
        align: "start",
    },
    {
        id: "navigation",
        target: { selector: TOUR_TARGETS.navigation },
        titleKey: "tour.steps.navigation.title",
        descriptionKey: "tour.steps.navigation.description",
        side: "bottom",
        align: "end",
    },
    {
        id: "menu",
        target: { selector: TOUR_TARGETS.menu },
        titleKey: "tour.steps.menu.title",
        descriptionKey: "tour.steps.menu.description",
        side: "bottom",
        align: "end",
    },
];
