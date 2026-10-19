import { describe, expect, it } from "vitest";

import {
    admitForPrefetch,
    LEAD_VIEWPORTS,
    prefetchWindow,
    rowsPerViewport,
    maxSpeculativeInFlight,
    scrollViewportsPerSecond,
    THUMBNAIL_NEIGHBOURS,
    thumbnailWarmRange,
    TRAIL_VIEWPORTS,
} from "./resultPrefetch";

const base = {
    range: { startIndex: 50, endIndex: 55 },
    count: 500,
    rowsPerViewport: 4,
    direction: "forward" as const,
    includeLead: true,
};

const LEAD = Math.ceil(LEAD_VIEWPORTS * base.rowsPerViewport);
const TRAIL = Math.ceil(TRAIL_VIEWPORTS * base.rowsPerViewport);

describe("prefetchWindow", () => {
    it("reports nothing before the list has said where it is", () => {
        expect(prefetchWindow({ ...base, range: null })).toBeNull();
    });

    it("reports nothing for an empty list", () => {
        expect(prefetchWindow({ ...base, count: 0 })).toBeNull();
    });

    it("leads ahead and trails behind when scrolling down", () => {
        expect(prefetchWindow(base)).toEqual({
            startIndex: 50 - TRAIL,
            endIndex: 55 + LEAD,
        });
    });

    it("puts the lead above when scrolling up", () => {
        expect(prefetchWindow({ ...base, direction: "backward" })).toEqual({
            startIndex: 50 - LEAD,
            endIndex: 55 + TRAIL,
        });
    });

    // Down is where a list is read, so the first scroll of a session should
    // already be warm ahead of the user rather than behind them.
    it("treats a list that has not moved yet as heading down", () => {
        expect(prefetchWindow({ ...base, direction: null })).toEqual(
            prefetchWindow({ ...base, direction: "forward" }),
        );
    });

    it("narrows to what is on screen when speculation is off", () => {
        expect(prefetchWindow({ ...base, includeLead: false })).toEqual({
            startIndex: 50,
            endIndex: 55,
        });
    });

    describe("the ends of the list", () => {
        it("does not reach above the first row", () => {
            const window = prefetchWindow({
                ...base,
                range: { startIndex: 0, endIndex: 3 },
                direction: "backward",
            });

            expect(window?.startIndex).toBe(0);
        });

        it("does not reach past the last row", () => {
            const window = prefetchWindow({
                ...base,
                range: { startIndex: 495, endIndex: 499 },
            });

            expect(window?.endIndex).toBe(499);
        });
    });

    // A screenful of tall cards is fewer rows than a screenful of short ones,
    // and the lead has to be the same amount of reading either way.
    it("scales the lead with how many rows fit on screen", () => {
        const tight = prefetchWindow({ ...base, rowsPerViewport: 2 });
        const loose = prefetchWindow({ ...base, rowsPerViewport: 8 });

        expect(loose!.endIndex - loose!.startIndex).toBeGreaterThan(
            tight!.endIndex - tight!.startIndex,
        );
    });

    it("still covers the visible rows when a screenful is one row", () => {
        const window = prefetchWindow({ ...base, rowsPerViewport: 0 });

        expect(window!.startIndex).toBeLessThanOrEqual(base.range.startIndex);
        expect(window!.endIndex).toBeGreaterThanOrEqual(base.range.endIndex);
    });
});

describe("rowsPerViewport", () => {
    it("counts how many rows a screenful holds", () => {
        expect(rowsPerViewport(800, 260)).toBe(4);
    });

    it("never reports less than one row", () => {
        expect(rowsPerViewport(100, 4_000)).toBe(1);
        expect(rowsPerViewport(800, 0)).toBe(1);
    });
});

describe("scrollViewportsPerSecond", () => {
    it("measures speed in screenfuls rather than pixels", () => {
        expect(scrollViewportsPerSecond(1_600, 1_000, 800)).toBe(2);
    });

    it("reads a scroll up as just as fast as a scroll down", () => {
        expect(scrollViewportsPerSecond(-1_600, 1_000, 800)).toBe(2);
    });

    // The unit matters: an unhurried read of a dense list is 16 rows a second
    // and a leisurely read of a loose one is 2, but both are well under a
    // screenful. Measuring in rows switched the lead off exactly where the
    // rows were shortest and most of them were needed.
    it("reads the same speed the same however tall the rows are", () => {
        expect(scrollViewportsPerSecond(640, 1_000, 800)).toBe(
            scrollViewportsPerSecond(640, 1_000, 800),
        );
        expect(scrollViewportsPerSecond(640, 1_000, 800)).toBeLessThan(1);
    });

    // Otherwise the first sample of a scroll reads as infinitely fast and
    // suppresses the very speculation it should be starting.
    it("is zero when no time has passed", () => {
        expect(scrollViewportsPerSecond(500, 0, 800)).toBe(0);
    });
});

describe("maxSpeculativeInFlight", () => {
    // A screen of a dense list is twenty rows rather than four, so that many
    // more are consumed per screenful of scrolling. A flat cap that keeps a
    // loose list ahead leaves a dense one permanently behind.
    it("asks for more at once when a screen holds more rows", () => {
        expect(maxSpeculativeInFlight(20)).toBeGreaterThan(
            maxSpeculativeInFlight(4),
        );
    });

    it("keeps a floor for a list of very tall rows", () => {
        expect(maxSpeculativeInFlight(1)).toBe(3);
    });

    // Past a point more concurrent requests only slow each other down, which
    // is the whole reason this cap exists.
    it("has a ceiling however dense the list gets", () => {
        expect(maxSpeculativeInFlight(500)).toBe(8);
    });
});

describe("admitForPrefetch", () => {
    // A visible card with nothing in it is the thing this exists to prevent,
    // and it is also the request most worth making.
    it("never holds back a row the user can see", () => {
        expect(
            admitForPrefetch({ onScreen: true, inFlight: 99, maxInFlight: 3 }),
        ).toBe(true);
    });

    it("lets speculation through while there is room", () => {
        expect(
            admitForPrefetch({ onScreen: false, inFlight: 2, maxInFlight: 3 }),
        ).toBe(true);
    });

    // Firing a whole window at once is what made the list worse than not
    // prefetching at all: the speculative requests went out alongside the ones
    // for rows being looked at, and all of them came back slower.
    it("holds speculation back once the cap is reached", () => {
        expect(
            admitForPrefetch({ onScreen: false, inFlight: 3, maxInFlight: 3 }),
        ).toBe(false);
    });
});

describe("thumbnailWarmRange", () => {
    const window = { startIndex: 40, endIndex: 70 };
    const base = {
        window,
        highlightedIndex: 50,
        thumbnailsShownOnEveryCard: true,
        count: 500,
    };

    // The image is part of the card being scrolled towards, so it is wanted
    // wherever the preview is.
    it("follows the preview window when every card shows a thumbnail", () => {
        expect(thumbnailWarmRange(base)).toEqual(window);
    });

    // With thumbnails off the window is irrelevant — none of those cards will
    // draw one. The only card that will is the highlighted one, and the arrow
    // keys say where the highlight is going.
    it("follows the highlight when only it shows a thumbnail", () => {
        expect(
            thumbnailWarmRange({
                ...base,
                thumbnailsShownOnEveryCard: false,
            }),
        ).toEqual({
            startIndex: 50 - THUMBNAIL_NEIGHBOURS,
            endIndex: 50 + THUMBNAIL_NEIGHBOURS,
        });
    });

    it("warms nothing with no highlight and no thumbnails on the cards", () => {
        expect(
            thumbnailWarmRange({
                ...base,
                thumbnailsShownOnEveryCard: false,
                highlightedIndex: -1,
            }),
        ).toBeNull();
    });

    it("stays inside the list at either end", () => {
        expect(
            thumbnailWarmRange({
                ...base,
                thumbnailsShownOnEveryCard: false,
                highlightedIndex: 0,
            })?.startIndex,
        ).toBe(0);
        expect(
            thumbnailWarmRange({
                ...base,
                thumbnailsShownOnEveryCard: false,
                highlightedIndex: 499,
            })?.endIndex,
        ).toBe(499);
    });

    it("warms nothing for an empty list", () => {
        expect(thumbnailWarmRange({ ...base, count: 0 })).toBeNull();
    });
});
