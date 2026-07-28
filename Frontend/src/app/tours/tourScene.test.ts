import { describe, expect, it } from "vitest";

import { LeftSidebarPanel, RightSidebarTab } from "@app/slices/searchSlice";

import { getTourLeftPanel, getTourRightTab } from "./tourScene";

describe("tour scenes", () => {
    it.each([
        ["folders", LeftSidebarPanel.FOLDER],
        ["tags", LeftSidebarPanel.TAGS],
        ["saved-queries", LeftSidebarPanel.QUERIES],
        ["bulk-actions", LeftSidebarPanel.BULK_ACTIONS],
        ["auto-actions", LeftSidebarPanel.AUTO_ACTIONS],
    ])("opens the %s left panel", (stepId, panel) => {
        expect(getTourLeftPanel(true, stepId)).toBe(panel);
        expect(getTourRightTab(true, stepId)).toBeNull();
    });

    it.each([
        ["statistics", RightSidebarTab.STATISTICS],
        ["chat", RightSidebarTab.CHAT],
    ])("opens the %s right panel", (stepId, tab) => {
        expect(getTourRightTab(true, stepId)).toBe(tab);
        expect(getTourLeftPanel(true, stepId)).toBeNull();
    });

    it("forces both sidebars closed for non-sidebar tour steps", () => {
        expect(getTourLeftPanel(true, "result-card")).toBeNull();
        expect(getTourRightTab(true, "result-card")).toBeNull();
    });

    it("leaves persisted sidebar state in control outside the tour", () => {
        expect(getTourLeftPanel(false, null)).toBeUndefined();
        expect(getTourRightTab(false, null)).toBeUndefined();
    });
});
