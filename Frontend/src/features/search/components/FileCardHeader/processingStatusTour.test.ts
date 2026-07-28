import { describe, expect, it } from "vitest";

import { hasVisibleProcessingStatus } from "./processingStatusTour";

describe("hasVisibleProcessingStatus", () => {
    it.each([
        {
            label: "truncated content on desktop",
            preview: {
                state: "processed",
                contentIsTruncated: true,
                attachmentsSkipped: false,
            },
            isMobile: false,
            expected: true,
        },
        {
            label: "skipped attachments on desktop",
            preview: {
                state: "processed",
                contentIsTruncated: false,
                attachmentsSkipped: true,
            },
            isMobile: false,
            expected: true,
        },
        {
            label: "hidden diagnostic icons on mobile",
            preview: {
                state: "processed",
                contentIsTruncated: true,
                attachmentsSkipped: true,
            },
            isMobile: true,
            expected: false,
        },
        {
            label: "failed state chip on mobile",
            preview: {
                state: "failed",
                contentIsTruncated: true,
                attachmentsSkipped: true,
            },
            isMobile: true,
            expected: true,
        },
    ])("returns $expected for $label", ({ expected, isMobile, preview }) => {
        expect(hasVisibleProcessingStatus(preview, isMobile)).toBe(expected);
    });
});
