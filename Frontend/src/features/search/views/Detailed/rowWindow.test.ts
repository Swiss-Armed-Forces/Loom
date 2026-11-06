import { describe, expect, it } from "vitest";

import { splitRowWindow } from "./rowWindow";

const rows = (...indexes: number[]) => indexes.map((index) => ({ index }));

describe("splitRowWindow", () => {
    it("keeps a contiguous range in one block", () => {
        const items = rows(10, 11, 12, 13);
        const { rows: block, pinned } = splitRowWindow(items, 11);
        expect(block).toBe(items);
        expect(pinned).toEqual([]);
    });

    it("takes a row pinned above the viewport out of the block", () => {
        const { rows: block, pinned } = splitRowWindow(
            rows(3, 200, 201, 202),
            201,
        );
        expect(block.map((item) => item.index)).toEqual([200, 201, 202]);
        expect(pinned.map((item) => item.index)).toEqual([3]);
    });

    it("takes a row pinned below the viewport out of the block", () => {
        const { rows: block, pinned } = splitRowWindow(
            rows(10, 11, 12, 400),
            10,
        );
        expect(block.map((item) => item.index)).toEqual([10, 11, 12]);
        expect(pinned.map((item) => item.index)).toEqual([400]);
    });

    it("keeps a pinned row adjacent to the viewport in the block", () => {
        const items = rows(9, 10, 11);
        expect(splitRowWindow(items, 10).rows).toBe(items);
    });
});
