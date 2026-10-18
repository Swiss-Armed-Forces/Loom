import { LeftSidebarPanel, RightSidebarTab } from "@app/slices/searchSlice";

/** Tabs of the left sidebar's customization panel. */
export type CustomizationTab = "card" | "actions" | "key";

const LEFT_PANEL_BY_STEP: Partial<Record<string, LeftSidebarPanel>> = {
    folders: LeftSidebarPanel.FOLDER,
    "folder-tree-node": LeftSidebarPanel.FOLDER,
    "folder-filter": LeftSidebarPanel.FOLDER,
    tags: LeftSidebarPanel.TAGS,
    "saved-queries": LeftSidebarPanel.QUERIES,
    "customization-card-display": LeftSidebarPanel.CUSTOMIZATION,
    "customization-card-fields": LeftSidebarPanel.CUSTOMIZATION,
    "customization-auto-actions": LeftSidebarPanel.CUSTOMIZATION,
    "customization-shortcuts": LeftSidebarPanel.CUSTOMIZATION,
    "chat-input": LeftSidebarPanel.CHAT,
    "chat-sources-warning": LeftSidebarPanel.CHAT,
    "chat-deep-search": LeftSidebarPanel.CHAT,
    "chat-history": LeftSidebarPanel.CHAT,
    "chat-new-chat": LeftSidebarPanel.CHAT,
};

/**
 * Which tab of the customization panel a step needs open.
 *
 * The panel's sections live behind tabs, so opening the panel is not enough
 * to put a step's target in the DOM - the same reason the steps above have to
 * name a sidebar panel.
 */
const CUSTOMIZATION_TAB_BY_STEP: Partial<Record<string, CustomizationTab>> = {
    "customization-card-display": "card",
    "customization-card-fields": "card",
    "customization-auto-actions": "actions",
    "customization-shortcuts": "key",
};

const RIGHT_TAB_BY_STEP: Partial<Record<string, RightSidebarTab>> = {
    "statistics-pie-chart": RightSidebarTab.STATISTICS,
    "statistics-histogram": RightSidebarTab.STATISTICS,
    "bulk-action-create-archive": RightSidebarTab.BULK_ACTIONS,
};

export const getTourLeftPanel = (
    isTourActive: boolean,
    activeStepId: string | null,
): LeftSidebarPanel | null | undefined =>
    isTourActive ? (LEFT_PANEL_BY_STEP[activeStepId ?? ""] ?? null) : undefined;

export const getTourCustomizationTab = (
    isTourActive: boolean,
    activeStepId: string | null,
): CustomizationTab | null =>
    isTourActive
        ? (CUSTOMIZATION_TAB_BY_STEP[activeStepId ?? ""] ?? null)
        : null;

export const getTourRightTab = (
    isTourActive: boolean,
    activeStepId: string | null,
): RightSidebarTab | null | undefined =>
    isTourActive ? (RIGHT_TAB_BY_STEP[activeStepId ?? ""] ?? null) : undefined;
