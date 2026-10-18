import { describe, expect, it } from "vitest";

import { columnWidthsOf, resizeColumns } from "./fieldColumns";

const total = (widths: number[]) => widths.reduce((sum, w) => sum + w, 0);

/** Widths come out of `fr` arithmetic, so they are compared as the floats
 *  they are rather than for equality. */
const rounded = (widths: number[]) => widths.map((w) => Number(w.toFixed(6)));

describe("resizeColumns", () => {
    it("takes from the neighbour what it gives, so the total never moves", () => {
        const next = resizeColumns([1, 1, 1, 1], 1, 0.3, 0.2);

        expect(rounded(next)).toEqual([1, 1.3, 0.7, 1]);
        // The thumbnail slot and the columns left alone keep their width only
        // because the dragged pair settles between themselves.
        expect(total(next)).toBeCloseTo(total([1, 1, 1, 1]));
    });

    it("stops at the minimum instead of collapsing a column", () => {
        const next = resizeColumns([1, 1], 0, 5, 0.2);

        expect(rounded(next)).toEqual([1.8, 0.2]);
        expect(total(next)).toBeCloseTo(2);
    });

    it("stops at the minimum when dragged the other way", () => {
        expect(rounded(resizeColumns([1, 1], 0, -5, 0.2))).toEqual([0.2, 1.8]);
    });

    it("refuses a drag whose pair cannot hold the minimum twice over", () => {
        const widths = [0.1, 0.1];

        // Nothing it could do here respects the minimum, so it leaves the
        // columns as they are rather than honouring one end and not the other.
        expect(resizeColumns(widths, 0, 0.05, 0.2)).toBe(widths);
    });

    it("leaves the widths alone when there is no column to the right", () => {
        const widths = [1, 1];

        expect(resizeColumns(widths, 1, 0.3, 0.2)).toBe(widths);
    });
});

describe("columnWidthsOf", () => {
    it("falls back to the default for a width that cannot be a track", () => {
        // Whatever is in local storage reaches the template unread; a single
        // one of these would otherwise invalidate it and collapse every
        // column of the list into one.
        const widths = {
            nan: Number.NaN,
            zero: 0,
            negative: -1,
            text: "wide" as unknown as number,
        };

        expect(
            columnWidthsOf(["nan", "zero", "negative", "text"], widths),
        ).toEqual([1, 1, 1, 1]);
    });

    it("keeps a dragged width with its field across a selection change", () => {
        const widths = { from: 2, subject: 0.5 };

        // "size" was never dragged and the order changed; from/subject keep
        // what they were given because widths are held per field, not per
        // position.
        expect(columnWidthsOf(["size", "subject", "from"], widths)).toEqual([
            1, 0.5, 2,
        ]);
    });
});
