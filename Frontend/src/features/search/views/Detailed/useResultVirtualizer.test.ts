import { describe, expect, it } from "vitest";

import { estimateFromMeasured } from "./useResultVirtualizer";

const FALLBACK = 260;

describe("estimateFromMeasured", () => {
    it("falls back while nothing has been measured", () => {
        expect(estimateFromMeasured([], FALLBACK, 256)).toBe(FALLBACK);
    });

    it("guesses high rather than average", () => {
        // One tall card among short ones. The mean would be 140, which places
        // the tall row's neighbour on top of it until it is measured; the
        // estimate has to err the other way, towards a gap that closes.
        const sizes = [100, 100, 100, 100, 400];

        const estimate = estimateFromMeasured(sizes, FALLBACK, 256);

        expect(estimate).toBeGreaterThan(100);
        expect(estimate).toBeLessThanOrEqual(400);
    });

    it("tracks the corpus rather than the starting guess", () => {
        // Rows measuring nothing like the constant they started from — short
        // mails where it expected scanned reports. The guess has to follow.
        const sizes = Array.from({ length: 40 }, () => 90);

        expect(estimateFromMeasured(sizes, FALLBACK, 256)).toBe(90);
    });

    it("stops after the sample cap", () => {
        // Everything past the cap is ignored, so the tail cannot move the
        // answer however long the list gets.
        const sizes = [...Array(4).fill(100), ...Array(1_000).fill(900)];

        expect(estimateFromMeasured(sizes, FALLBACK, 4)).toBe(100);
    });
});
