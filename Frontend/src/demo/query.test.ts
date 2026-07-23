import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { parseDemoQuery } from "./query";
import { type DemoDocument } from "./repository";

const document = (
    size: number,
    uploadedAt = "2026-06-02T12:00:00Z",
): DemoDocument => ({
    archiveIds: [],
    authors: [],
    content: "A small document",
    createdAt: uploadedAt,
    data: "A small document",
    extension: "txt",
    flagged: false,
    hidden: false,
    id: "11111111-1111-4111-8111-111111111111",
    language: "en",
    mimeType: "text/plain",
    modifiedAt: uploadedAt,
    name: "document.txt",
    path: "/document.txt",
    seen: false,
    secrets: [],
    size,
    source: "api-upload",
    state: "processed",
    summary: "A summary",
    tags: [],
    uploadedAt,
});

describe("demo query evaluator", () => {
    beforeEach(() => vi.useFakeTimers());
    afterEach(() => vi.useRealTimers());

    it("uses decimal size suffixes like the backend", () => {
        const query = parseDemoQuery("size:>1M");

        expect(query.matches(document(1_010_000))).toBe(true);
        expect(query.matches(document(990_000))).toBe(false);
    });

    it("evaluates every supported relative date keyword", () => {
        vi.setSystemTime("2026-06-17T12:00:00Z");
        const matches = (query: string, uploadedAt: string) =>
            parseDemoQuery(query).matches(document(1, uploadedAt));

        expect(matches("modified:today", "2026-06-17T08:00:00Z")).toBe(true);
        expect(matches("modified:today", "2026-06-16T08:00:00Z")).toBe(false);
        expect(matches("modified:yesterday", "2026-06-16T08:00:00Z")).toBe(
            true,
        );
        expect(matches("modified:yesterday", "2026-06-15T08:00:00Z")).toBe(
            false,
        );
        expect(matches("modified:thisweek", "2026-06-15T08:00:00Z")).toBe(true);
        expect(matches("modified:thisweek", "2026-06-14T08:00:00Z")).toBe(
            false,
        );
        expect(matches("modified:thismonth", "2026-06-01T08:00:00Z")).toBe(
            true,
        );
        expect(matches("modified:thismonth", "2026-05-31T08:00:00Z")).toBe(
            false,
        );
        expect(matches("modified:thisyear", "2026-01-01T08:00:00Z")).toBe(true);
        expect(matches("modified:thisyear", "2025-12-31T08:00:00Z")).toBe(
            false,
        );
    });

    it("returns only fields containing an unfielded text match", () => {
        const highlights = parseDemoQuery("small").highlights(document(1));

        expect(highlights).toEqual({
            content: ["A <highlight>small</highlight> document"],
        });
    });

    it("resolves field aliases without adding unrelated attributes", () => {
        const highlights = parseDemoQuery("filename:document.txt").highlights(
            document(1),
        );

        expect(Object.keys(highlights)).toEqual([
            "short_name",
            "short_name.keyword",
            "full_name",
            "full_name.keyword",
            "full_path",
            "full_path.keyword",
        ]);
        expect(highlights).not.toHaveProperty("content");
        expect(highlights).not.toHaveProperty("size");
    });

    it("omits match-all, negated, existence, range, and comparison filters", () => {
        const fixture = document(2_000_000);
        fixture.tags = ["interesting"];

        expect(parseDemoQuery("*").highlights(fixture)).toEqual({});
        expect(parseDemoQuery("NOT tags:missing").highlights(fixture)).toEqual(
            {},
        );
        expect(parseDemoQuery("summary:*").highlights(fixture)).toEqual({});
        expect(parseDemoQuery("size:>1M").highlights(fixture)).toEqual({});
        expect(
            parseDemoQuery("uploaded:[* TO 2027-01-01]").highlights(fixture),
        ).toEqual({});
    });

    it("combines only matching positive boolean branches", () => {
        const fixture = document(1);
        fixture.tags = ["interesting"];

        expect(
            parseDemoQuery("tags:interesting OR tags:missing").highlights(
                fixture,
            ),
        ).toEqual({ tags: ["<highlight>interesting</highlight>"] });
        expect(
            parseDemoQuery("small AND NOT tags:missing").highlights(fixture),
        ).toEqual({
            content: ["A <highlight>small</highlight> document"],
        });
    });

    it("highlights regex, wildcard, fuzzy, and proximity matches", () => {
        const fixture = document(1);

        expect(parseDemoQuery("/sm.ll/").highlights(fixture).content).toEqual([
            "A <highlight>small</highlight> document",
        ]);
        expect(parseDemoQuery("sm*").highlights(fixture).content).toEqual([
            "A <highlight>sm</highlight>all document",
        ]);
        expect(parseDemoQuery("smoll~1").highlights(fixture).content).toEqual([
            "A <highlight>small</highlight> document",
        ]);
        expect(
            parseDemoQuery('"A document"~1').highlights(fixture).content,
        ).toEqual([
            "<highlight>A</highlight> small <highlight>document</highlight>",
        ]);
    });
});
