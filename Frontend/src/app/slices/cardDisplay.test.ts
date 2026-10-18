import { describe, expect, it } from "vitest";

import reducer, {
    DENSITY_PRESETS,
    SearchState,
    applyDensityPreset,
    selectCardElementVisibility,
    selectMatchingDensityPreset,
    setAutoDetectedDensity,
    setCardDensity,
    setShowThumbnails,
} from "./searchSlice";

const stateWith = (overrides: Partial<SearchState>): SearchState =>
    ({
        cardDensity: "auto",
        autoDetectedDensity: "standard",
        ...DENSITY_PRESETS.standard,
        ...overrides,
    }) as SearchState;

const select = (state: SearchState) =>
    selectMatchingDensityPreset({ search: state } as never);

describe("card display: spacing and elements as two axes", () => {
    it("leaves the elements alone when only the spacing changes", () => {
        const before = stateWith({ showThumbnails: true });

        const after = reducer(before, setCardDensity("compact"));

        // The compact preset switches thumbnails off; asking for compact
        // *spacing* must not, or the two controls are one control again.
        expect(after.showThumbnails).toBe(true);
        expect(after.cardDensity).toBe("compact");
    });

    it("sets both axes when a preset is applied", () => {
        const after = reducer(
            stateWith({ showThumbnails: true }),
            applyDensityPreset("compact"),
        );

        expect(after.cardDensity).toBe("compact");
        expect(selectCardElementVisibility({ search: after } as never)).toEqual(
            DENSITY_PRESETS.compact,
        );
    });

    it("keeps the spacing where it is when an element is switched", () => {
        const after = reducer(
            stateWith({ cardDensity: "full", ...DENSITY_PRESETS.full }),
            setShowThumbnails(false),
        );

        // This is what the "custom" density used to do, and why the spacing
        // silently reverted to standard on every switch.
        expect(after.cardDensity).toBe("full");
        expect(after.showThumbnails).toBe(false);
    });
});

describe("the preset a card reads as", () => {
    it("takes the auto preset to the look the window resolved to", () => {
        const after = reducer(
            stateWith({
                cardDensity: "full",
                autoDetectedDensity: "compact",
                ...DENSITY_PRESETS.full,
            }),
            applyDensityPreset("auto"),
        );

        // Picking "auto" has to light "auto" up, which it only does when the
        // switches come along with the spacing.
        expect(after.cardDensity).toBe("auto");
        expect(selectCardElementVisibility({ search: after } as never)).toEqual(
            DENSITY_PRESETS.compact,
        );
        expect(select(after)).toBe("compact");
    });

    it("names the preset while the switches still match it", () => {
        expect(
            select(
                stateWith({
                    autoDetectedDensity: "compact",
                    ...DENSITY_PRESETS.compact,
                }),
            ),
        ).toBe("compact");
    });

    it("names none once a switch has been taken off the preset", () => {
        expect(
            select(
                stateWith({
                    cardDensity: "full",
                    ...DENSITY_PRESETS.full,
                    showTags: !DENSITY_PRESETS.full.showTags,
                }),
            ),
        ).toBeNull();
    });
});

describe("auto spacing", () => {
    it("re-applies the detected preset while nothing has been customised", () => {
        const before = stateWith({ ...DENSITY_PRESETS.standard });

        const after = reducer(before, setAutoDetectedDensity("full"));

        expect(after.showThumbnails).toBe(DENSITY_PRESETS.full.showThumbnails);
    });

    it("never overwrites a switch the user set", () => {
        const before = stateWith({
            ...DENSITY_PRESETS.standard,
            showThumbnails: true,
        });

        const after = reducer(before, setAutoDetectedDensity("compact"));

        // A window resize is not an instruction about what to show.
        expect(after.showThumbnails).toBe(true);
        expect(after.autoDetectedDensity).toBe("compact");
    });

    it("leaves the elements alone when the spacing is pinned", () => {
        const before = stateWith({
            cardDensity: "full",
            ...DENSITY_PRESETS.full,
        });

        const after = reducer(before, setAutoDetectedDensity("compact"));

        expect(after.showThumbnails).toBe(DENSITY_PRESETS.full.showThumbnails);
    });
});
