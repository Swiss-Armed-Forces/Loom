import { describe, expect, it } from "vitest";

import { shouldShowFilePanel, shouldShowSearchPanel } from "./panelVisibility";

describe("center tab panel visibility", () => {
    it("temporarily shows Results instead of the active file during a tour", () => {
        expect(shouldShowSearchPanel("file-1", true)).toBe(true);
        expect(shouldShowFilePanel("file-1", "file-1", true)).toBe(false);
    });

    it("restores the selected file panel after the tour", () => {
        expect(shouldShowSearchPanel("file-1", false)).toBe(false);
        expect(shouldShowFilePanel("file-1", "file-1", false)).toBe(true);
    });

    it("keeps Results visible when no file tab is selected", () => {
        expect(shouldShowSearchPanel(null, false)).toBe(true);
        expect(shouldShowFilePanel("file-1", null, false)).toBe(false);
    });
});
