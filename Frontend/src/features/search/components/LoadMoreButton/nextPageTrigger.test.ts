import { describe, expect, it } from "vitest";

import { PAGE_LEAD_ROWS, shouldFetchNextPage } from "./nextPageTrigger";

const loaded = 100;
const base = {
    visibleRange: { startIndex: 10, endIndex: 15 },
    loadedCount: loaded,
    hasMore: true,
    isPaginating: false,
    hasError: false,
};

/** The last row index that is still too far from the end to trigger. */
const beforeLead = loaded - 2 - PAGE_LEAD_ROWS;

describe("shouldFetchNextPage", () => {
    it("waits while the user is in the middle of what is loaded", () => {
        expect(shouldFetchNextPage(base)).toBe(false);
    });

    it("fetches once the end comes within the lead", () => {
        expect(
            shouldFetchNextPage({
                ...base,
                visibleRange: { startIndex: 90, endIndex: beforeLead + 1 },
            }),
        ).toBe(true);
    });

    it("does not fetch one row short of the lead", () => {
        expect(
            shouldFetchNextPage({
                ...base,
                visibleRange: { startIndex: 80, endIndex: beforeLead },
            }),
        ).toBe(false);
    });

    // The sentinel this replaced could not see this case at all: with nothing
    // to scroll, it never came into view and the list sat half empty.
    it("fills a list shorter than the viewport", () => {
        expect(
            shouldFetchNextPage({
                ...base,
                loadedCount: 3,
                visibleRange: { startIndex: 0, endIndex: 2 },
            }),
        ).toBe(true);
    });

    it("stops at the end of the results", () => {
        expect(
            shouldFetchNextPage({
                ...base,
                hasMore: false,
                visibleRange: { startIndex: 90, endIndex: 99 },
            }),
        ).toBe(false);
    });

    it("does not stack a second request on the one in flight", () => {
        expect(
            shouldFetchNextPage({
                ...base,
                isPaginating: true,
                visibleRange: { startIndex: 90, endIndex: 99 },
            }),
        ).toBe(false);
    });

    // Retrying a failing request once per scroll would hammer the API, and the
    // button is what takes over.
    it("stays out of the way after a failure", () => {
        expect(
            shouldFetchNextPage({
                ...base,
                hasError: true,
                visibleRange: { startIndex: 90, endIndex: 99 },
            }),
        ).toBe(false);
    });

    it("waits until the list has reported where it is", () => {
        expect(shouldFetchNextPage({ ...base, visibleRange: null })).toBe(
            false,
        );
    });

    it("does nothing with nothing loaded", () => {
        expect(
            shouldFetchNextPage({
                ...base,
                loadedCount: 0,
                visibleRange: { startIndex: 0, endIndex: 0 },
            }),
        ).toBe(false);
    });
});
