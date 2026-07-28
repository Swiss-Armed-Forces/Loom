import { LeftSidebarPanel, RightSidebarTab } from "@app/slices/searchSlice";

const LEFT_PANEL_BY_STEP: Partial<Record<string, LeftSidebarPanel>> = {
    folders: LeftSidebarPanel.FOLDER,
    "folder-tree-node": LeftSidebarPanel.FOLDER,
    "folder-filter": LeftSidebarPanel.FOLDER,
    tags: LeftSidebarPanel.TAGS,
    "saved-queries": LeftSidebarPanel.QUERIES,
    "bulk-actions": LeftSidebarPanel.BULK_ACTIONS,
    "auto-actions": LeftSidebarPanel.AUTO_ACTIONS,
};

const RIGHT_TAB_BY_STEP: Partial<Record<string, RightSidebarTab>> = {
    statistics: RightSidebarTab.STATISTICS,
    "statistics-pie-chart": RightSidebarTab.STATISTICS,
    "statistics-histogram": RightSidebarTab.STATISTICS,
    chat: RightSidebarTab.CHAT,
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
