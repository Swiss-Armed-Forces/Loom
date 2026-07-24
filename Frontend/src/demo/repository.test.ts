import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SearchQueryField } from "@features/common/utils/enums";
import { updateFieldOfQuery } from "@features/common/utils/helpers";
import { SEARCH_TIPS } from "@features/search/components/EmptySearchResults/searchTips";

import {
    addArchive,
    addTags,
    clearDemoTimers,
    getArchives,
    getDocument,
    getDocuments,
    getMetrics,
    getTags,
    removeTag,
    resetDemoRepository,
    scheduleTask,
    searchDocuments,
    updateDocument,
} from "./repository";

describe("demo repository", () => {
    beforeEach(() => {
        vi.useFakeTimers();
        resetDemoRepository();
    });

    afterEach(() => {
        clearDemoTimers();
        vi.useRealTimers();
    });

    it("returns the nine visible integration fixtures by default", () => {
        expect(searchDocuments("")).toHaveLength(9);
        expect(searchDocuments("*")).toHaveLength(9);
        expect(getDocuments()).toHaveLength(10);
    });

    it("bundles safe fixtures while redacting sensitive and executable payloads", () => {
        const image = searchDocuments('file_type:"image/png"')[0];
        const secretFixture = searchDocuments("secrets:*")[0];
        const installer = searchDocuments("state:failed")[0];

        expect(image).toMatchObject({
            name: "1.png",
            size: 10_552,
            downloadUrl: expect.any(String),
            thumbnail: {
                url: expect.any(String),
                totalFrames: 1,
            },
            rendered: { imageUrl: expect.any(String) },
        });
        expect(secretFixture.secrets).toEqual([
            "database-password",
            "generic-api-key",
            "slack-webhook",
        ]);
        expect(secretFixture.data).not.toContain(
            "8f9d0f4e3c2a7b1d6e5f0c3a8d7e6f5a",
        );
        expect(installer).toMatchObject({
            name: "test_installer.msi",
            size: 2_572_288,
        });
        expect(installer.downloadUrl).toBeUndefined();
    });

    it("only exposes renderer artifacts that Loom produces for each file type", () => {
        const text = searchDocuments('filename:"John Smith*"')[0];
        const email = searchDocuments("filename:basic_email.eml")[0];
        const office = searchDocuments("filename:sample3.docx")[0];
        const archive = searchDocuments("filename:testarchive_larger.zip")[0];

        expect(text).toMatchObject({
            thumbnail: { totalFrames: 1 },
            rendered: { officePdfUrl: expect.any(String) },
        });
        expect(email).toMatchObject({
            thumbnail: { totalFrames: 1 },
            rendered: {
                imageUrl: expect.any(String),
                officePdfUrl: expect.any(String),
            },
        });
        expect(office).toMatchObject({
            thumbnail: { totalFrames: 1 },
            rendered: { officePdfUrl: expect.any(String) },
        });
        expect(archive.thumbnail).toBeUndefined();
        expect(archive.rendered).toBeUndefined();
    });

    it("matches content keywords and common metadata filters", () => {
        expect(
            searchDocuments("network security").map((item) => item.extension),
        ).toEqual(["txt"]);
        expect(
            searchDocuments("plain email").map((item) => item.extension),
        ).toEqual(["eml"]);
        expect(searchDocuments("tags:interesting")).toHaveLength(3);
        expect(searchDocuments("extension:docx")).toHaveLength(1);
        expect(searchDocuments("NOT state:processed")).toHaveLength(2);
    });

    it("evaluates boolean groups, wildcards, comparisons, and ranges", () => {
        expect(searchDocuments("email OR security")).toHaveLength(3);
        expect(
            searchDocuments('tags:("networking" OR "accessibility")').map(
                (item) => item.extension,
            ),
        ).toEqual(["txt", "docx"]);
        expect(searchDocuments("filename:basic_*")).toHaveLength(1);
        expect(searchDocuments("size:>1M")).toHaveLength(1);
        expect(
            searchDocuments("uploaded_datetime:[* TO 2020-06-15]").map(
                (item) => item.extension,
            ),
        ).toEqual(["eml"]);
        expect(
            searchDocuments(
                "tika_meta.dcterms_created:{2020-12-31 TO 2025-01-01}",
            ).map((item) => item.extension),
        ).toEqual(["zip"]);
    });

    it("treats quoted boolean words as search terms", () => {
        expect(() => searchDocuments('"OR"')).not.toThrow();
    });

    it.each(SEARCH_TIPS)(
        "returns a result for the advertised query $query",
        ({ query }) => {
            expect(searchDocuments(query).length).toBeGreaterThan(0);
        },
    );

    it("supports regex, fuzzy, phrase proximity, and special field selectors", () => {
        expect(searchDocuments("/.*Jo?n.*/")).toHaveLength(1);
        expect(searchDocuments("Lindsar~1")).toHaveLength(1);
        expect(searchDocuments('"John security"~2')).toHaveLength(1);
        expect(searchDocuments('"John security"~1')).toHaveLength(0);
        expect(searchDocuments("*:John")).toHaveLength(1);
        expect(searchDocuments("\\*name\\*:*txt*")).toHaveLength(3);
        expect(searchDocuments("summary:*")).toHaveLength(9);
    });

    it("resolves relative dates against the current browser date", () => {
        vi.setSystemTime("2026-06-02T18:00:00Z");
        resetDemoRepository();

        expect(
            searchDocuments("modified:today").map((item) => item.extension),
        ).toEqual(["txt"]);
    });

    it("supports grouped filters generated by statistics interactions", () => {
        expect(
            searchDocuments('tags:("interesting" OR "accessibility")'),
        ).toHaveLength(4);
        expect(searchDocuments('NOT extension:("zip" OR "docx")')).toHaveLength(
            7,
        );
    });

    it("accepts grouped and negated filters emitted by the frontend helper", () => {
        const grouped = updateFieldOfQuery("*", SearchQueryField.Tags, [
            "interesting",
            "accessibility",
        ]);
        const negated = updateFieldOfQuery(
            grouped,
            SearchQueryField.Extension,
            "png",
            false,
            true,
        );

        expect(searchDocuments(grouped)).toHaveLength(4);
        expect(searchDocuments(negated).map((item) => item.extension)).toEqual([
            "txt",
            "eml",
            "docx",
        ]);
    });

    it("rejects malformed expressions instead of silently returning no data", () => {
        expect(() => searchDocuments("tags:")).toThrow("Missing value");
        expect(() => searchDocuments("(email OR security")).toThrow(
            "Unterminated query group",
        );
        expect(() => searchDocuments("/(security).*/")).toThrow(
            "Regular expression uses syntax unsupported",
        );
        expect(() => searchDocuments("security~3")).toThrow(
            "Fuzzy distance must be between 0 and 2",
        );
    });

    it("updates document state and tags within the session", () => {
        const id = searchDocuments('filename:"John Smith*"')[0].id;
        updateDocument(id, { seen: true, flagged: false });
        addTags(id, ["reviewed"]);
        expect(getDocument(id)).toMatchObject({ seen: true, flagged: false });
        expect(getTags()).toContain("reviewed");
        removeTag(id, "reviewed");
        expect(getDocument(id)?.tags).not.toContain("reviewed");
    });

    it("creates archives and resets all mutations on reload", () => {
        const archive = addArchive("tags:security");
        expect(getArchives()).toHaveLength(2);
        expect(searchDocuments(`archives:${archive.id}`)).toHaveLength(1);
        resetDemoRepository();
        expect(getArchives()).toHaveLength(1);
    });

    it("keeps diagnostics bounded while background work completes", () => {
        resetDemoRepository();
        const initial = getMetrics().messagesInQueues;
        const id = searchDocuments("tags:security")[0].id;
        scheduleTask(id, { kind: "summarize" });
        expect(getMetrics().messagesInQueues).toBe(initial + 1);
        vi.advanceTimersByTime(2_100);
        expect(getMetrics().messagesInQueues).toBe(0);
    });

    it("finishes the seeded processing document and becomes idle", () => {
        resetDemoRepository();

        expect(getMetrics().messagesInQueues).toBe(1);
        expect(searchDocuments("state:processing")).toHaveLength(1);

        vi.advanceTimersByTime(2_100);

        expect(getMetrics().messagesInQueues).toBe(0);
        expect(searchDocuments("state:processing")).toHaveLength(0);
    });

    it("cancels scheduled work when the repository resets", () => {
        resetDemoRepository();
        const id = searchDocuments("tags:security")[0].id;
        scheduleTask(id, { kind: "summarize" });
        expect(getMetrics().messagesInQueues).toBe(2);
        resetDemoRepository();
        vi.advanceTimersByTime(2_100);
        expect(getMetrics().messagesInQueues).toBe(0);
    });

    it("uses the requested language for translation tasks", () => {
        const document = searchDocuments("tags:security")[0];

        scheduleTask(document.id, { kind: "translate", language: "de" });
        vi.advanceTimersByTime(2_100);

        expect(getDocument(document.id)?.language).toBe("de");
    });
});
