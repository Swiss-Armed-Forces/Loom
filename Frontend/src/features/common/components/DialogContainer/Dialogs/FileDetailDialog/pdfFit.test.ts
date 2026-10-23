import { describe, expect, it } from "vitest";

import { shouldFitToWidth } from "./pdfFit";

describe("shouldFitToWidth", () => {
    it("does not fit a container that has no width yet", () => {
        // The case that strands pdf.js at an unset scale, which the first
        // zoom then multiplies and clamps to the minimum.
        expect(shouldFitToWidth(0, false)).toBe(false);
    });

    it("fits once the container has a width", () => {
        expect(shouldFitToWidth(1200, false)).toBe(true);
    });

    it("leaves a document that has been fitted alone", () => {
        // A resize must not take back a zoom the reader chose.
        expect(shouldFitToWidth(1200, true)).toBe(false);
    });
});
