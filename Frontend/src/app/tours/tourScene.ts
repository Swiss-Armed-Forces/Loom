import { LeftSidebarPanel, RightSidebarTab } from "@app/slices/searchSlice";

const LEFT_PANEL_BY_STEP: Partial<Record<string, LeftSidebarPanel>> = {
    folders: LeftSidebarPanel.FOLDER,
    "folder-tree-node": LeftSidebarPanel.FOLDER,
    "folder-filter": LeftSidebarPanel.FOLDER,
    tags: LeftSidebarPanel.TAGS,
    "saved-queries": LeftSidebarPanel.QUERIES,
    "card-customization-display": LeftSidebarPanel.CARD_CUSTOMIZATION,
    "card-customization-fields": LeftSidebarPanel.CARD_CUSTOMIZATION,
    "card-customization-auto-actions": LeftSidebarPanel.CARD_CUSTOMIZATION,
    "chat-input": LeftSidebarPanel.CHAT,
    "chat-sources-warning": LeftSidebarPanel.CHAT,
    "chat-deep-search": LeftSidebarPanel.CHAT,
    "chat-history": LeftSidebarPanel.CHAT,
    "chat-new-chat": LeftSidebarPanel.CHAT,
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

export const getTourRightTab = (
    isTourActive: boolean,
    activeStepId: string | null,
): RightSidebarTab | null | undefined =>
    isTourActive ? (RIGHT_TAB_BY_STEP[activeStepId ?? ""] ?? null) : undefined;
