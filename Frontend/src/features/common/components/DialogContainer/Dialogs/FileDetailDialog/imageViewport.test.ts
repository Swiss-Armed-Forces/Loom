import { describe, expect, it } from "vitest";

import {
    anchoredPan,
    clampPan,
    isPannable,
    renderedSize,
    topAnchoredPan,
} from "./imageViewport";

const FRAME = { width: 400, height: 300 };

describe("renderedSize", () => {
    it("scales both axes with the zoom", () => {
        // act
        const result = renderedSize({ width: 100, height: 50 }, 2, 0);

        // assert
        expect(result).toEqual({ width: 200, height: 100 });
    });

    it("keeps the axes at a half turn", () => {
        // act
        const result = renderedSize({ width: 100, height: 50 }, 1, 180);

        // assert
        expect(result).toEqual({ width: 100, height: 50 });
    });

    it("swaps the axes at a quarter turn", () => {
        // act
        const atNinety = renderedSize({ width: 100, height: 50 }, 1, 90);
        const atTwoSeventy = renderedSize({ width: 100, height: 50 }, 1, 270);

        // assert
        expect(atNinety).toEqual({ width: 50, height: 100 });
        expect(atTwoSeventy).toEqual({ width: 50, height: 100 });
    });
});

describe("isPannable", () => {
    it("is false while the image fits on both axes", () => {
        // act
        const result = isPannable({ width: 400, height: 300 }, FRAME);

        // assert
        expect(result).toBe(false);
    });

    it("is true as soon as one axis sticks out", () => {
        // act
        const result = isPannable({ width: 400, height: 301 }, FRAME);

        // assert
        expect(result).toBe(true);
    });
});

describe("clampPan", () => {
    it("pins the pan to the frame while the image fits", () => {
        // act
        const result = clampPan(
            { x: 120, y: -80 },
            { width: 400, height: 300 },
            FRAME,
        );

        // assert: a zero width window, so the image cannot be nudged at all.
        expect(result.x).toBeCloseTo(0);
        expect(result.y).toBeCloseTo(0);
    });

    it("allows exactly the half that hangs out of the frame", () => {
        // act
        const result = clampPan(
            { x: 999, y: -999 },
            { width: 600, height: 500 },
            FRAME,
        );

        // assert
        expect(result).toEqual({ x: 100, y: -100 });
    });

    it("leaves a pan inside the bounds untouched", () => {
        // act
        const result = clampPan(
            { x: 30, y: -40 },
            { width: 600, height: 500 },
            FRAME,
        );

        // assert
        expect(result).toEqual({ x: 30, y: -40 });
    });
});

describe("topAnchoredPan", () => {
    it("offsets by the half that hangs out above the frame", () => {
        // act
        const result = topAnchoredPan({ width: 400, height: 500 }, FRAME);

        // assert
        expect(result).toEqual({ x: 0, y: 100 });
    });

    it("stays centred while the image fits", () => {
        // act
        const result = topAnchoredPan({ width: 400, height: 200 }, FRAME);

        // assert
        expect(result).toEqual({ x: 0, y: 0 });
    });
});

describe("anchoredPan", () => {
    it("keeps an off-centre anchor over the same pixel while zooming in", () => {
        // arrange
        const pan = { x: 20, y: -35 };
        const anchorOffset = { x: 120, y: -60 };
        const ratio = 1.15;

        // act
        const result = anchoredPan(pan, anchorOffset, ratio);

        // assert: the anchor's distance from the image centre grew by exactly
        // the zoom ratio, which is what keeps the pixel under the cursor.
        expect(result.x - anchorOffset.x).toBeCloseTo(
            (pan.x - anchorOffset.x) * ratio,
        );
        expect(result.y - anchorOffset.y).toBeCloseTo(
            (pan.y - anchorOffset.y) * ratio,
        );
    });

    it("keeps an off-centre anchor over the same pixel while zooming out", () => {
        // arrange
        const pan = { x: 20, y: -35 };
        const anchorOffset = { x: 120, y: -60 };
        const ratio = 1 / 1.15;

        // act
        const result = anchoredPan(pan, anchorOffset, ratio);

        // assert
        expect(result.x - anchorOffset.x).toBeCloseTo(
            (pan.x - anchorOffset.x) * ratio,
        );
        expect(result.y - anchorOffset.y).toBeCloseTo(
            (pan.y - anchorOffset.y) * ratio,
        );
    });

    it("does not move the image when the zoom is clamped at a bound", () => {
        // arrange: a clamped zoom yields a ratio of exactly 1.
        const pan = { x: 20, y: -35 };

        // act
        const result = anchoredPan(pan, { x: 120, y: -60 }, 1);

        // assert
        expect(result).toEqual(pan);
    });

    it("scales the pan itself when the anchor is the frame centre", () => {
        // act
        const result = anchoredPan({ x: 20, y: -35 }, { x: 0, y: 0 }, 2);

        // assert
        expect(result).toEqual({ x: 40, y: -70 });
    });
});
