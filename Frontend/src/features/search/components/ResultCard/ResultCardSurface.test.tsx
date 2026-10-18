import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { globalTheme } from "@app/theme";

import { ResultCardSurface } from "./ResultCardSurface";
import {
    resultCardElevation,
    resultCardSurfaceStyle,
} from "./resultCardSurfaceStyle";

interface RenderedSurface {
    readState: string | null | undefined;
    cursor: string | null | undefined;
}

const surfaceOf = (props: {
    seen: boolean;
    isHighlighted?: boolean;
}): RenderedSurface => {
    const { container } = render(
        <ResultCardSurface
            seen={props.seen}
            isHighlighted={props.isHighlighted ?? false}
        >
            <span>card body</span>
        </ResultCardSurface>,
    );
    const card = container.querySelector("[data-read-state]");
    return {
        readState: card?.getAttribute("data-read-state"),
        cursor: card?.getAttribute("data-cursor"),
    };
};

describe("ResultCardSurface", () => {
    it("treats an unseen file's card as unread", () => {
        expect(surfaceOf({ seen: false }).readState).toBe("unread");
    });

    it("leaves a seen file's card without the unread treatment", () => {
        expect(surfaceOf({ seen: true }).readState).toBe("read");
    });

    it("marks the highlighted card as the cursor", () => {
        expect(surfaceOf({ seen: true, isHighlighted: true }).cursor).toBe(
            "true",
        );
    });

    it("keeps the unread state on the highlighted card", () => {
        // The highlight marks one card out of the list while unread may apply
        // to most of it, so the cursor must not consume the unread marking of
        // the card it happens to sit on.
        expect(surfaceOf({ seen: false, isHighlighted: true })).toEqual({
            readState: "unread",
            cursor: "true",
        });
    });

    it("does not publish the highlight as data-highlighted", () => {
        const { container } = render(
            <ResultCardSurface seen={false} isHighlighted>
                <span>card body</span>
            </ResultCardSurface>,
        );
        // That attribute identifies the enclosing `.resultCardParent` for the
        // keyboard navigation's document-wide lookups.
        expect(container.querySelector("[data-highlighted]")).toBeNull();
    });
});

describe("resultCardSurfaceStyle", () => {
    const styleOf = (isHighlighted: boolean, unread: boolean, flat = false) =>
        resultCardSurfaceStyle({ isHighlighted, unread, flat }, globalTheme);

    it("marks unread with the left bar and nothing else", () => {
        const unread = styleOf(false, true);
        const read = styleOf(false, false);

        expect(unread.borderColor).not.toBe("transparent");
        expect(read.borderColor).toBe("transparent");
        // Read state applies to every file in the list, so it may not claim
        // the surface - that belongs to the one highlighted card.
        expect(unread.bgcolor).toBeUndefined();
        expect(unread.boxShadow).toBeUndefined();
    });

    it("tints and glows the highlighted card and nothing else", () => {
        const highlighted = styleOf(true, false);

        expect(highlighted.bgcolor).toBeTruthy();
        expect(highlighted.boxShadow).toBeTruthy();
        expect(styleOf(false, false).bgcolor).toBeUndefined();
        expect(styleOf(false, false).boxShadow).toBeUndefined();
    });

    it("tints and glows in the shared amber", () => {
        const highlighted = styleOf(true, false);

        expect(highlighted.bgcolor).toContain("palette-primary");
        expect(highlighted.boxShadow).toContain("palette-primary");
    });

    it("keeps the elevation shadow the glow is composed onto", () => {
        // `box-shadow` is a single property: writing only the glow would drop
        // the card's elevation instead of adding to it.
        expect(styleOf(true, false).boxShadow).toContain("shadows-8");
    });

    it("spreads the glow evenly rather than dropping it to one side", () => {
        // A halo surrounds the card; an offset would read as another drop
        // shadow on top of the elevation it is composed onto.
        expect(styleOf(true, false).boxShadow).toContain("0 0 ");
    });

    it("lifts the highlighted card above the list", () => {
        expect(resultCardElevation(true, false)).toBeGreaterThan(
            resultCardElevation(false, false),
        );
    });

    it("keeps the cursor inside the card in a gapless list", () => {
        // A halo needs clear space around the card. Where the rows meet, the
        // blur would land on the neighbouring rows instead.
        const flat = styleOf(true, false, true);

        expect(flat.boxShadow).toContain("inset");
        expect(flat.boxShadow).toContain("palette-primary");
        expect(flat.bgcolor).toBeTruthy();
    });

    it("does not lift a card that has nowhere to lift into", () => {
        // The drop shadow of a gapless row falls on the row below it.
        expect(resultCardElevation(true, true)).toBe(0);
        expect(resultCardElevation(false, true)).toBe(0);
    });

    it("resolves every colour to a real theme token", () => {
        // `rgba(undefined / 0.55)` is a silently invisible cue, so assert the
        // channel tokens these interpolate actually exist.
        const { boxShadow, bgcolor } = styleOf(true, true);

        expect(boxShadow).not.toContain("undefined");
        expect(bgcolor).not.toContain("undefined");
    });

    it("keeps the bar independent of the highlight", () => {
        // The two channels may not read each other's input: that is what lets
        // an unread card survive being highlighted.
        for (const unread of [true, false]) {
            expect(styleOf(true, unread).borderColor).toBe(
                styleOf(false, unread).borderColor,
            );
        }
    });

    it("keeps the cursor cues independent of the read state", () => {
        expect(styleOf(true, true).bgcolor).toBe(styleOf(true, false).bgcolor);
        expect(styleOf(true, true).boxShadow).toBe(
            styleOf(true, false).boxShadow,
        );
    });
});
