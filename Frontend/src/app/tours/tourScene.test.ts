import { describe, expect, it } from "vitest";

import { LeftSidebarPanel, RightSidebarTab } from "@app/slices/searchSlice";

import { getTourLeftPanel, getTourRightTab } from "./tourScene";

describe("tour scenes", () => {
    it.each([
        ["folders", LeftSidebarPanel.FOLDER],
        ["tags", LeftSidebarPanel.TAGS],
        ["saved-queries", LeftSidebarPanel.QUERIES],
        ["card-customization-display", LeftSidebarPanel.CARD_CUSTOMIZATION],
        ["card-customization-fields", LeftSidebarPanel.CARD_CUSTOMIZATION],
        [
            "card-customization-auto-actions",
            LeftSidebarPanel.CARD_CUSTOMIZATION,
        ],
        ["chat-input", LeftSidebarPanel.CHAT],
        ["chat-history", LeftSidebarPanel.CHAT],
        ["chat-new-chat", LeftSidebarPanel.CHAT],
    ])("opens the %s left panel", (stepId, panel) => {
        expect(getTourLeftPanel(true, stepId)).toBe(panel);
        expect(getTourRightTab(true, stepId)).toBeNull();
    });

    it.each([
        ["statistics-pie-chart", RightSidebarTab.STATISTICS],
        ["statistics-histogram", RightSidebarTab.STATISTICS],
    ])("opens the %s right panel", (stepId, tab) => {
        expect(getTourRightTab(true, stepId)).toBe(tab);
        expect(getTourLeftPanel(true, stepId)).toBeNull();
    });

    it.each([
        "result-card",
        "filtered-folder",
        "statistics",
        "bulk-actions",
        "card-customization",
        "chat",
    ])("forces both sidebars closed for the %s tour step", (stepId) => {
        expect(getTourLeftPanel(true, stepId)).toBeNull();
        expect(getTourRightTab(true, stepId)).toBeNull();
    });

    it("leaves persisted sidebar state in control outside the tour", () => {
        expect(getTourLeftPanel(false, null)).toBeUndefined();
        expect(getTourRightTab(false, null)).toBeUndefined();
    });
});
