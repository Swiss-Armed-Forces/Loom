import { describe, expect, it } from "vitest";

import { getFormattedDateTime } from "./getFormattedDateTime";

describe("getFormattedDateTime", () => {
    it("puts the month before the day", () => {
        // 22 October, the case where a transposition is visible at all.
        expect(getFormattedDateTime("2026-10-22T01:13:00")).toMatch(
            /^2026-10-22 /,
        );
    });

    it("is unambiguous on a day the month could be mistaken for", () => {
        expect(getFormattedDateTime("2026-03-05T09:30:00")).toMatch(
            /^2026-03-05 /,
        );
    });
});
