import { describe, expect, it } from "vitest";

import { estimateFromMeasured, measureNonZero } from "./useResultVirtualizer";

const FALLBACK = 260;

/** A virtualizer with one row measured, as `measureNonZero` reads it. */
const instanceWith = (cached?: number) =>
    ({
        indexFromElement: () => 7,
        itemSizeCache: new Map(cached === undefined ? [] : [["row-7", cached]]),
        options: {
            horizontal: false,
            getItemKey: (index: number) => `row-${index}`,
            estimateSize: () => FALLBACK,
        },
    }) as never;

const reported = (blockSize: number) =>
    ({ borderBoxSize: [{ blockSize, inlineSize: 0 }] }) as never;

describe("measureNonZero", () => {
    it("takes the height the row reports", () => {
        expect(
            measureNonZero(null as never, reported(180), instanceWith(90)),
        ).toBe(180);
    });

    it("keeps the measured height when a hidden row reports nothing", () => {
        // A row inside a panel that has been switched away from has no layout
        // box. Recording the zero shrinks the list under the reader.
        expect(
            measureNonZero(null as never, reported(0), instanceWith(90)),
        ).toBe(90);
    });

    it("falls back to the estimate for a row never measured", () => {
        expect(measureNonZero(null as never, reported(0), instanceWith())).toBe(
            FALLBACK,
        );
    });
});

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
