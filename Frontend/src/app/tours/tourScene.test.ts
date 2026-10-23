import { describe, expect, it } from "vitest";

import { LeftSidebarPanel, RightSidebarTab } from "@app/slices/searchSlice";

import { getTourLeftPanel, getTourRightTab } from "./tourScene";

describe("tour scenes", () => {
    it.each([
        ["folders", LeftSidebarPanel.FOLDER],
        ["tags", LeftSidebarPanel.TAGS],
        ["saved-queries", LeftSidebarPanel.QUERIES],
        ["customization-card-display", LeftSidebarPanel.CUSTOMIZATION],
        ["customization-card-fields", LeftSidebarPanel.CUSTOMIZATION],
        ["customization-auto-actions", LeftSidebarPanel.CUSTOMIZATION],
        ["customization-shortcuts", LeftSidebarPanel.CUSTOMIZATION],
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
        "customization",
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

describe("steps whose target lives in the right sidebar", () => {
    // A step that names no tab is shown with the sidebar shut, so a detail
    // step that forgot to name one would wait out its timeout on an element
    // that was never going to appear.
    it.each([
        "file-detail",
        "file-detail-tabs",
        "document-detail",
        "detail-rendered",
        "detail-translations",
        "detail-highlights",
        "detail-raw",
    ])("opens the File Detail sidebar for %s", (stepId) => {
        expect(getTourRightTab(true, stepId)).toBe(RightSidebarTab.FILE_DETAIL);
    });
});
