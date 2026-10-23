import { describe, expect, it } from "vitest";

import { GetFilePreviewResponse } from "@app/api";

import {
    apiPreviewFields,
    indicatorMarks,
    isIndicatorField,
} from "./indicatorFields";

const PREVIEW = {
    fileId: "f1",
    flagged: true,
    hidden: false,
    seen: false,
    name: "mail.eml",
    path: "/Mail/Inbox/mail.eml",
    fileExtension: "eml",
    state: "indexed",
    tags: ["invoice", "2026"],
    attachmentsTotalCount: 3,
} as GetFilePreviewResponse;

describe("apiPreviewFields", () => {
    it("keeps the backend's fields and drops the indicators", () => {
        // The indicators are drawn from the preview the request already
        // returns. Asking for them would ask for a field the backend has
        // never heard of.
        expect(
            apiPreviewFields(["content", "loom:icons", "short_name"]),
        ).toEqual(["content", "short_name"]);
    });

    it("leaves a selection of ordinary fields untouched", () => {
        expect(apiPreviewFields(["content"])).toEqual(["content"]);
    });
});

describe("isIndicatorField", () => {
    it("does not claim a backend field that reads like one", () => {
        expect(isIndicatorField("state")).toBe(false);
        expect(isIndicatorField("loom:state")).toBe(true);
    });
});

describe("indicatorMarks", () => {
    it("draws a mark for each thing the file carries", () => {
        expect(indicatorMarks("loom:icons", PREVIEW)).toEqual([
            "attachments",
            "flagged",
            "unseen",
            "tags",
        ]);
    });

    it("drops the unseen dot once the file has been read", () => {
        const seen = { ...PREVIEW, seen: true } as GetFilePreviewResponse;

        expect(indicatorMarks("loom:icons", seen)).not.toContain("unseen");
    });

    it("reads a preview that carries none of them as bare", () => {
        // `tags` and `attachmentsTotalCount` are both optional on the
        // response, so absent has to mean none rather than a lit icon.
        const bare = {
            ...PREVIEW,
            flagged: false,
            seen: true,
        } as GetFilePreviewResponse;
        delete bare.tags;
        delete bare.attachmentsTotalCount;

        expect(indicatorMarks("loom:icons", bare)).toEqual([]);
        expect(indicatorMarks("loom:status", bare)).toEqual([]);
    });

    it("keeps each field to its own marks", () => {
        const flagged = {
            ...PREVIEW,
            contentIsTruncated: true,
            isSpam: true,
        } as GetFilePreviewResponse;

        expect(indicatorMarks("loom:status", flagged)).toEqual([
            "truncated",
            "spam",
        ]);
        // The state is a value, not a presence, and is drawn by the renderer
        // from the preview rather than counted here.
        expect(indicatorMarks("loom:state", flagged)).toEqual([]);
    });
});
