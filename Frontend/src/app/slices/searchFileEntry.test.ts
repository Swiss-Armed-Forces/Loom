import { describe, expect, it } from "vitest";

import type { SearchQuery } from "@features/common/utils/model";

import {
    isPreviewFresh,
    PREVIEW_REVALIDATE_MS,
    SearchFileEntry,
} from "./searchFileEntry";

const query = (text: string): SearchQuery => ({
    id: "pit-1",
    query: text,
    keepAlive: null,
    sortField: null,
    sortDirection: null,
    sortId: null,
    pageSize: null,
});

const NOW = 1_700_000_000_000;

const entry = (overrides: Partial<SearchFileEntry> = {}): SearchFileEntry => ({
    meta: null,
    preview: { fileId: "f-1" } as SearchFileEntry["preview"],
    query: query("foo"),
    previewFields: ["content"],
    previewFetchedAt: NOW,
    ...overrides,
});

const freshness = (overrides = {}) => ({
    query: query("foo"),
    previewFields: ["content"],
    now: NOW,
    ...overrides,
});

describe("isPreviewFresh", () => {
    it("accepts an entry matching the query, the field set and the TTL", () => {
        expect(isPreviewFresh(entry(), freshness())).toBe(true);
    });

    it("rejects a missing entry", () => {
        expect(isPreviewFresh(undefined, freshness())).toBe(false);
    });

    it("rejects an entry with no preview yet", () => {
        expect(isPreviewFresh(entry({ preview: null }), freshness())).toBe(
            false,
        );
    });

    it("rejects a stale entry", () => {
        expect(isPreviewFresh(entry({ stale: true }), freshness())).toBe(false);
    });

    it("rejects a preview fetched for another query", () => {
        expect(
            isPreviewFresh(entry({ query: query("bar") }), freshness()),
        ).toBe(false);
    });

    describe("field set", () => {
        // The reason this predicate exists: changing which fields cards show
        // used to re-fetch only the previews that happened to be on screen at
        // that moment, and every other entry kept serving the old set.
        it("rejects a preview fetched for a different field set", () => {
            expect(
                isPreviewFresh(
                    entry({ previewFields: ["content"] }),
                    freshness({ previewFields: ["content", "summary"] }),
                ),
            ).toBe(false);
        });

        it("accepts the same fields in a different order", () => {
            expect(
                isPreviewFresh(
                    entry({ previewFields: ["summary", "content"] }),
                    freshness({ previewFields: ["content", "summary"] }),
                ),
            ).toBe(true);
        });

        it("rejects an entry predating field tracking", () => {
            expect(
                isPreviewFresh(
                    entry({ previewFields: undefined }),
                    freshness(),
                ),
            ).toBe(false);
        });
    });

    describe("revalidation", () => {
        it("accepts a preview inside the TTL", () => {
            expect(
                isPreviewFresh(
                    entry({
                        previewFetchedAt: NOW - PREVIEW_REVALIDATE_MS + 1,
                    }),
                    freshness(),
                ),
            ).toBe(true);
        });

        it("rejects a preview past the TTL", () => {
            expect(
                isPreviewFresh(
                    entry({ previewFetchedAt: NOW - PREVIEW_REVALIDATE_MS }),
                    freshness(),
                ),
            ).toBe(false);
        });

        it("rejects an entry with no fetch timestamp", () => {
            expect(
                isPreviewFresh(
                    entry({ previewFetchedAt: undefined }),
                    freshness(),
                ),
            ).toBe(false);
        });
    });
});
