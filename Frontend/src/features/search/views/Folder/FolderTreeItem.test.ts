import { describe, expect, it } from "vitest";

import { FolderTree } from "./folderViewState";
import { hasUnloadedChildren } from "./util";

const node = (overrides: Partial<FolderTree> = {}): FolderTree => ({
    id: "/Research",
    label: "Research",
    ...overrides,
});

describe("hasUnloadedChildren", () => {
    it("does not treat a file count as evidence that a file has children", () => {
        expect(
            hasUnloadedChildren(
                node({
                    id: "/Research/report.txt",
                    label: "report.txt",
                    fileCount: 1,
                    fileId: "file-1",
                }),
            ),
        ).toBe(false);
    });

    it("marks an unloaded non-empty directory as expandable", () => {
        expect(hasUnloadedChildren(node({ fileCount: 1 }))).toBe(true);
    });
});
