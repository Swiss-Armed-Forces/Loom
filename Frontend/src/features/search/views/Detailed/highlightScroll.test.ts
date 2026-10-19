import { describe, expect, it } from "vitest";

import { alignForHighlight, SCROLL_PADDING_PX } from "./highlightScroll";

const VIEWPORT_HEIGHT = 800;
const BAND = VIEWPORT_HEIGHT - 2 * SCROLL_PADDING_PX;

describe("alignForHighlight", () => {
    describe("smart", () => {
        it("leaves a card that fits in the band to the virtualizer", () => {
            // "auto" is the dead band: a card already clear of the padding at
            // both ends stays exactly where it is, so walking the list does
            // not drag the viewport along behind a perfectly readable card.
            expect(alignForHighlight(200, VIEWPORT_HEIGHT, "smart")).toBe(
                "auto",
            );
        });

        it("treats a card exactly filling the band as fitting", () => {
            expect(alignForHighlight(BAND, VIEWPORT_HEIGHT, "smart")).toBe(
                "auto",
            );
        });

        it("aligns a card too tall for the band to the top", () => {
            // Aligning its bottom would put its beginning off screen.
            expect(alignForHighlight(BAND + 1, VIEWPORT_HEIGHT, "smart")).toBe(
                "start",
            );
        });
    });

    it("aligns to the top on a jump from elsewhere, however the card fits", () => {
        expect(alignForHighlight(200, VIEWPORT_HEIGHT, "top")).toBe("start");
    });
});
