import { describe, expect, it } from "vitest";

import {
    FOLLOW_TAB,
    fileTab,
    sameSelection,
    selectedFileIdOf,
    selectionKey,
} from "./fileDetailSelection";

describe("sameSelection", () => {
    it("tells the following tab from a file's", () => {
        expect(sameSelection(FOLLOW_TAB, fileTab("a"))).toBe(false);
        expect(sameSelection(fileTab("a"), FOLLOW_TAB)).toBe(false);
    });

    it("compares file tabs by their file", () => {
        expect(sameSelection(fileTab("a"), fileTab("a"))).toBe(true);
        expect(sameSelection(fileTab("a"), fileTab("b"))).toBe(false);
    });
});

describe("selectedFileIdOf", () => {
    it("reads the following tab's file off the highlight", () => {
        expect(selectedFileIdOf(FOLLOW_TAB, "a")).toBe("a");
    });

    it("is empty only for the following tab with nothing highlighted", () => {
        // The one state in which the sidebar has a tab but no file, and so
        // the one state that draws the placeholder.
        expect(selectedFileIdOf(FOLLOW_TAB, null)).toBeNull();
        expect(selectedFileIdOf(fileTab("a"), null)).toBe("a");
    });

    it("leaves a file tab alone whatever is highlighted", () => {
        expect(selectedFileIdOf(fileTab("a"), "b")).toBe("a");
    });
});

describe("selectionKey", () => {
    it("cannot collide a file with the following tab", () => {
        // A file genuinely named "follow" would otherwise share a key with
        // the tab that has no file at all.
        expect(selectionKey(fileTab("follow"))).not.toBe(
            selectionKey(FOLLOW_TAB),
        );
    });
});
