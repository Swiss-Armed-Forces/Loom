import { describe, expect, it } from "vitest";

import {
    depthOfNode,
    isWithinExtractionLimit,
    isWithinLimits,
    shouldLoadChildrenOf,
} from "./depthLimits";
import { FolderTree } from "./folderViewState";
import { findTreeNode } from "./util";

const nodeAt = (path: string): FolderTree => {
    const node = findTreeNode(archiveTree, path);
    if (node === undefined) throw new Error(`no such fixture node: ${path}`);
    return node;
};

/** The shape the two rules disagree about: an archive whose entries Tika hands
 *  back under their own inner folder. `testfile01.txt` is three path levels
 *  below the zip but only one container hop inside it. */
const archiveTree: FolderTree = {
    id: "/",
    label: "/",
    children: {
        "//s/Crawler": {
            id: "//s/Crawler",
            label: "Crawler",
            children: {
                "//s/Crawler/a.zip": {
                    id: "//s/Crawler/a.zip",
                    label: "a.zip",
                    fileId: "zip-1",
                    children: {
                        "//s/Crawler/a.zip/inner": {
                            id: "//s/Crawler/a.zip/inner",
                            label: "inner",
                            children: {
                                "//s/Crawler/a.zip/inner/testfile01.txt": {
                                    id: "//s/Crawler/a.zip/inner/testfile01.txt",
                                    label: "testfile01.txt",
                                    fileId: "txt-1",
                                },
                            },
                        },
                        "//s/Crawler/a.zip/bundle.zip": {
                            id: "//s/Crawler/a.zip/bundle.zip",
                            label: "bundle.zip",
                            fileId: "zip-2",
                            children: {
                                "//s/Crawler/a.zip/bundle.zip/report.pdf": {
                                    id: "//s/Crawler/a.zip/bundle.zip/report.pdf",
                                    label: "report.pdf",
                                    fileId: "pdf-1",
                                },
                            },
                        },
                    },
                },
            },
        },
    },
};

describe("path depth", () => {
    it("draws a node at the limit and stops below it", () => {
        const limits = { pathDepth: 2, extractionDepth: null };
        expect(isWithinLimits({ path: 2, extraction: 0 }, limits)).toBe(true);
        expect(isWithinLimits({ path: 3, extraction: 0 }, limits)).toBe(false);
    });
});

describe("extraction depth", () => {
    it("counts containers rather than path segments", () => {
        // The archive's inner folder is a path level, not a container.
        expect(
            depthOfNode(archiveTree, "//s/Crawler/a.zip/inner")?.extraction,
        ).toBe(1);
        expect(
            depthOfNode(archiveTree, "//s/Crawler/a.zip/inner/testfile01.txt")
                ?.extraction,
        ).toBe(1);
        // Its path is one segment shorter, yet it is one container deeper.
        expect(
            depthOfNode(archiveTree, "//s/Crawler/a.zip/bundle.zip/report.pdf")
                ?.extraction,
        ).toBe(2);
    });

    it("leaves a file that came straight from the source at zero", () => {
        expect(depthOfNode(archiveTree, "//s/Crawler/a.zip")?.extraction).toBe(
            0,
        );
    });

    it("hides everything extracted when the limit is none", () => {
        const limits = { pathDepth: null, extractionDepth: 0 };
        expect(isWithinLimits({ path: 9, extraction: 0 }, limits)).toBe(true);
        expect(isWithinLimits({ path: 2, extraction: 1 }, limits)).toBe(false);
    });
});

describe("the two limits together", () => {
    it("requires a node to pass both", () => {
        const limits = { pathDepth: 3, extractionDepth: 1 };
        expect(isWithinLimits({ path: 3, extraction: 1 }, limits)).toBe(true);
        expect(isWithinLimits({ path: 4, extraction: 1 }, limits)).toBe(false);
        expect(isWithinLimits({ path: 3, extraction: 2 }, limits)).toBe(false);
    });
});

describe("fetching children", () => {
    it("skips a generation the limits would hide", () => {
        expect(
            shouldLoadChildrenOf(archiveTree, nodeAt("//s/Crawler/a.zip"), {
                pathDepth: null,
                extractionDepth: 0,
            }),
        ).toBe(false);
    });

    it("does not hold back a node that is within the limits", () => {
        expect(
            shouldLoadChildrenOf(archiveTree, nodeAt("//s/Crawler"), {
                pathDepth: 3,
                extractionDepth: 0,
            }),
        ).toBe(true);
    });
});

describe("the flat filter list", () => {
    it("reads nesting off the row, having no ancestors to count", () => {
        const limits = { pathDepth: 1, extractionDepth: 1 };
        // The folder limit must not reach the flat list: it is not a tree.
        expect(isWithinExtractionLimit(1, limits)).toBe(true);
        expect(isWithinExtractionLimit(2, limits)).toBe(false);
    });

    it("treats a row with no reported nesting as not extracted", () => {
        expect(
            isWithinExtractionLimit(undefined, {
                pathDepth: null,
                extractionDepth: 0,
            }),
        ).toBe(true);
    });
});
