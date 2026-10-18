import { describe, expect, it } from "vitest";

import { moveItem } from "./moveItem";

describe("moveItem", () => {
    it("moves an entry forward, closing the gap behind it", () => {
        expect(moveItem(["a", "b", "c", "d"], 0, 2)).toEqual([
            "b",
            "c",
            "a",
            "d",
        ]);
    });

    it("moves an entry back", () => {
        expect(moveItem(["a", "b", "c", "d"], 3, 1)).toEqual([
            "a",
            "d",
            "b",
            "c",
        ]);
    });

    it("keeps every entry exactly once", () => {
        const fields = ["content", "created", "from", "subject"];

        const moved = moveItem(fields, 3, 0);

        // The list being reordered is the set of fields the cards request;
        // losing or doubling one would change what is fetched, not just the
        // order it is shown in.
        expect([...moved].sort()).toEqual([...fields].sort());
    });

    it("gives the same array back for a move that changes nothing", () => {
        const fields = ["a", "b"];

        expect(moveItem(fields, 1, 1)).toBe(fields);
        expect(moveItem(fields, -1, 0)).toBe(fields);
        expect(moveItem(fields, 0, 5)).toBe(fields);
    });
});
