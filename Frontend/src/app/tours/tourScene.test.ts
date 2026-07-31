import { describe, expect, it } from "vitest";

import { LeftSidebarPanel, RightSidebarTab } from "@app/slices/searchSlice";

import { getTourLeftPanel, getTourRightTab } from "./tourScene";

describe("tour scenes", () => {
    it.each([
        ["folders", LeftSidebarPanel.FOLDER],
        ["tags", LeftSidebarPanel.TAGS],
        ["saved-queries", LeftSidebarPanel.QUERIES],
        ["auto-actions", LeftSidebarPanel.AUTO_ACTIONS],
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
        "chat",
        "bulk-actions",
    ])("forces both sidebars closed for the %s tour step", (stepId) => {
        expect(getTourLeftPanel(true, stepId)).toBeNull();
        expect(getTourRightTab(true, stepId)).toBeNull();
    });

    it("leaves persisted sidebar state in control outside the tour", () => {
        expect(getTourLeftPanel(false, null)).toBeUndefined();
        expect(getTourRightTab(false, null)).toBeUndefined();
    });
});
