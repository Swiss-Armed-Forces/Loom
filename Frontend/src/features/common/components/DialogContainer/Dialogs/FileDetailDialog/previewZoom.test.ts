import { describe, expect, it } from "vitest";

import { wheelDeltaInPixels, wheelZoomFactor } from "./previewZoom";

describe("wheelDeltaInPixels", () => {
    it("passes pixel deltas through unchanged", () => {
        // act
        const result = wheelDeltaInPixels(120, WheelEvent.DOM_DELTA_PIXEL, 800);

        // assert
        expect(result).toBe(120);
    });

    it("converts Firefox's line deltas to pixels", () => {
        // act
        const result = wheelDeltaInPixels(3, WheelEvent.DOM_DELTA_LINE, 800);

        // assert
        expect(result).toBe(48);
    });

    it("converts page deltas with the size of the viewport", () => {
        // act
        const result = wheelDeltaInPixels(2, WheelEvent.DOM_DELTA_PAGE, 800);

        // assert
        expect(result).toBe(1600);
    });

    it("keeps the sign of the delta on every mode", () => {
        // assert
        expect(
            wheelDeltaInPixels(-3, WheelEvent.DOM_DELTA_LINE, 800),
        ).toBeLessThan(0);
        expect(
            wheelDeltaInPixels(-2, WheelEvent.DOM_DELTA_PAGE, 800),
        ).toBeLessThan(0);
        expect(
            wheelDeltaInPixels(-120, WheelEvent.DOM_DELTA_PIXEL, 800),
        ).toBeLessThan(0);
    });
});

describe("wheelZoomFactor", () => {
    it("zooms in on a negative delta and out on a positive one", () => {
        // assert
        expect(wheelZoomFactor(-100)).toBeGreaterThan(1);
        expect(wheelZoomFactor(100)).toBeLessThan(1);
    });

    it("does not change the zoom without a delta", () => {
        // assert
        expect(wheelZoomFactor(0)).toBe(1);
    });

    it("is symmetric, so a delta and its opposite cancel out", () => {
        // assert
        expect(wheelZoomFactor(37) * wheelZoomFactor(-37)).toBeCloseTo(1);
    });

    it("bounds a single event, so a page sized delta cannot teleport", () => {
        // act
        const pageDelta = wheelDeltaInPixels(1, WheelEvent.DOM_DELTA_PAGE, 800);

        // assert
        expect(wheelZoomFactor(pageDelta)).toBe(wheelZoomFactor(200));
        expect(wheelZoomFactor(-pageDelta)).toBe(wheelZoomFactor(-200));
    });

    it("scales with the delta, so many small steps equal one big one", () => {
        // act
        const inTenSteps = Math.pow(wheelZoomFactor(-10), 10);

        // assert
        expect(inTenSteps).toBeCloseTo(wheelZoomFactor(-100));
    });
});
