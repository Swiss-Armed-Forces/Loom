import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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
            onToggleSeen={vi.fn()}
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

    it("toggles the read state from the bar without disturbing the card", () => {
        // The card's own click highlights the file, and highlighting it marks
        // it seen under the `markAsSeen` auto-action, so a bar click that
        // bubbled would mark a file seen in the gesture that marked it unseen.
        const onToggleSeen = vi.fn();
        const onCardClick = vi.fn();
        render(
            <div onClick={onCardClick}>
                <ResultCardSurface
                    seen={false}
                    isHighlighted={false}
                    onToggleSeen={onToggleSeen}
                >
                    <span>card body</span>
                </ResultCardSurface>
            </div>,
        );

        fireEvent.click(screen.getByLabelText("seen"));

        expect(onToggleSeen).toHaveBeenCalledTimes(1);
        expect(onCardClick).not.toHaveBeenCalled();
    });

    it("does not publish the highlight as data-highlighted", () => {
        const { container } = render(
            <ResultCardSurface
                seen={false}
                isHighlighted
                onToggleSeen={vi.fn()}
            >
                <span>card body</span>
            </ResultCardSurface>,
        );
        // That attribute identifies the enclosing `.resultCardParent` for the
        // keyboard navigation's document-wide lookups.
        expect(container.querySelector("[data-highlighted]")).toBeNull();
    });
});

describe("resultCardSurfaceStyle", () => {
    /** The dark scheme's block, as `theme.applyStyles` renders it. */
    const DARK_SCHEME = "@media (prefers-color-scheme: dark)";

    const styleOf = (isHighlighted: boolean, unread: boolean) =>
        resultCardSurfaceStyle({ isHighlighted, unread }, globalTheme);

    it("marks unread with the left bar and nothing else", () => {
        const unread = styleOf(false, true);
        const read = styleOf(false, false);

        expect(unread.borderColor).not.toBe("transparent");
        expect(read.borderColor).toBe("transparent");
        // Read state applies to every file in the list, so it may not claim
        // the surface - that belongs to the one highlighted card.
        expect(unread.tint).toEqual({});
    });

    it("tints the highlighted card and nothing else", () => {
        // The tint is the whole mark. An edge of any kind - ring, halo,
        // border - reads as a different kind of card rather than the same
        // card under the cursor, and it changes the shape of the one row the
        // reader is looking at.
        expect(styleOf(true, false).tint.backgroundColor).toBeTruthy();
        expect(styleOf(false, false).tint).toEqual({});
        expect(Object.keys(styleOf(true, false))).toEqual([
            "borderColor",
            "tint",
        ]);
    });

    it("tints in the shared amber", () => {
        expect(JSON.stringify(styleOf(true, false).tint)).toContain(
            "palette-primary",
        );
    });

    it("washes each colour scheme at its own strength", () => {
        // Both schemes share one primary and differ only in `background`, so
        // a single alpha is not the same wash over a light card as it is over
        // the dark card's paper.
        const { tint } = styleOf(true, false);

        expect(tint[DARK_SCHEME]).toEqual({
            backgroundColor: expect.any(String),
        });
        expect(tint[DARK_SCHEME]).not.toEqual({
            backgroundColor: tint.backgroundColor,
        });
    });

    it("sits every card at the same height", () => {
        // Lifting the highlighted card above the list on a deeper shadow is
        // one more way for it to differ from its neighbours.
        expect(resultCardElevation(false)).toBeGreaterThan(0);
        expect(resultCardElevation(true)).toBe(0);
    });

    it("resolves the tint to a real theme token", () => {
        // `rgba(undefined / 0.2)` is a silently invisible cue, so assert the
        // channel token every scheme interpolates actually exists.
        expect(JSON.stringify(styleOf(true, true).tint)).not.toContain(
            "undefined",
        );
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

    it("keeps the cursor cue independent of the read state", () => {
        expect(styleOf(true, true).tint).toEqual(styleOf(true, false).tint);
    });
});
