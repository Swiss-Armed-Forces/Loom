import { describe, expect, it } from "vitest";

import {
    getColorFromString,
    getFontColorFromBackGroundColor,
} from "./getColorFromString";

const channels = (hex: string) => [
    parseInt(hex.substring(1, 3), 16),
    parseInt(hex.substring(3, 5), 16),
    parseInt(hex.substring(5, 7), 16),
];

const luminance = (hex: string) =>
    channels(hex)
        .map((v) => v / 255)
        .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
        .reduce((sum, c, i) => sum + [0.2126, 0.7152, 0.0722][i] * c, 0);

const contrast = (a: string, b: string) => {
    const [l1, l2] = [luminance(a) + 0.05, luminance(b) + 0.05];
    return Math.max(l1, l2) / Math.min(l1, l2);
};

// Every colour a tag can be given, taken through the same hash the chips use.
const paletteColours = () => {
    const seen = new Set<string>();
    for (let i = 0; i < 4000; i += 1) seen.add(getColorFromString(`tag-${i}`));
    return [...seen];
};

describe("getFontColorFromBackGroundColor", () => {
    it("keeps every tag colour at or above the 4.5:1 text minimum", () => {
        const failures = paletteColours()
            .map((bg) => ({
                bg,
                ratio: contrast(bg, getFontColorFromBackGroundColor(bg)),
            }))
            .filter(({ ratio }) => ratio < 4.5);
        expect(failures).toEqual([]);
    });

    it("picks whichever of black and white reads better", () => {
        for (const bg of paletteColours()) {
            const chosen = getFontColorFromBackGroundColor(bg);
            const other = chosen === "#000000" ? "#ffffff" : "#000000";
            expect(contrast(bg, chosen)).toBeGreaterThanOrEqual(
                contrast(bg, other),
            );
        }
    });
});
