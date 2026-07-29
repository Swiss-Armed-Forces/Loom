import { describe, expect, it } from "vitest";

import { FolderTree } from "./folderViewState";
import { hasUnloadedChildren } from "./util";

const node = (overrides: Partial<FolderTree> = {}): FolderTree => ({
    id: "/Research",
    label: "Research",
    ...overrides,
});

describe("hasUnloadedChildren", () => {
    it("marks an unloaded non-empty directory as expandable", () => {
        expect(hasUnloadedChildren(node({ fileCount: 1 }))).toBe(true);
    });

    it("marks a file node with extracted children (e.g. an archive) as expandable", () => {
        expect(
            hasUnloadedChildren(
                node({
                    id: "/Documents/archive.zip",
                    label: "archive.zip",
                    fileCount: 3,
                    fileId: "file-1",
                }),
            ),
        ).toBe(true);
    });

    it("does not mark a leaf file with no children as expandable", () => {
        expect(
            hasUnloadedChildren(
                node({
                    id: "/Research/report.txt",
                    label: "report.txt",
                    fileCount: 0,
                    fileId: "file-1",
                }),
            ),
        ).toBe(false);
    });

    it("does not mark an already-loaded node as expandable", () => {
        expect(hasUnloadedChildren(node({ fileCount: 5, children: {} }))).toBe(
            false,
        );
    });

    it("does not mark a loading node as expandable", () => {
        expect(hasUnloadedChildren(node({ fileCount: 5, loading: true }))).toBe(
            false,
        );
    });
});
