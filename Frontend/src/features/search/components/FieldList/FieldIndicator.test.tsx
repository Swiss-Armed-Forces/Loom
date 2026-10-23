import { ThemeProvider } from "@mui/material/styles";
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { GetFilePreviewResponse } from "@app/api";
import { globalTheme } from "@app/theme";

import { FieldIndicator } from "./FieldIndicator";
import { IndicatorFieldId } from "./indicatorFields";

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

const PREVIEW = {
    fileId: "f1",
    flagged: true,
    hidden: false,
    seen: false,
    name: "mail.eml",
    path: "/Mail/Inbox/mail.eml",
    fileExtension: "eml",
    state: "processed",
    tags: ["invoice"],
    attachmentsTotalCount: 3,
} as GetFilePreviewResponse;

const renderIndicator = (
    fieldId: IndicatorFieldId,
    preview: GetFilePreviewResponse = PREVIEW,
) =>
    render(
        <ThemeProvider theme={globalTheme}>
            <FieldIndicator fieldId={fieldId} filePreview={preview} />
        </ThemeProvider>,
    ).container;

const iconTitles = (container: HTMLElement) =>
    [...container.querySelectorAll("svg title")].map((t) => t.textContent);

describe("FieldIndicator", () => {
    it("draws every mark the file carries on one row", () => {
        // Four things that each used to cost a line of their own.
        expect(iconTitles(renderIndicator("loom:icons"))).toEqual([
            "fieldSections.mark.attachments",
            "fieldSections.mark.flagged",
            "fieldSections.mark.unseen",
            "fieldSections.mark.tags",
        ]);
    });

    it("draws nothing for a mark the file does not carry", () => {
        // Not a muted icon and not the label on its own: the mark being there
        // is the answer, so anything in its place would have to be read
        // before it could be dismissed.
        expect(iconTitles(renderIndicator("loom:status"))).toEqual([]);
    });

    it("colours a flag red and the rest not", () => {
        const icons = renderIndicator("loom:icons").querySelectorAll("svg");
        const colour = (i: number) => getComputedStyle(icons[i]).color;

        expect(colour(1)).toBe("var(--mui-palette-error-main)");
        expect(colour(0)).toBe("var(--mui-palette-text-secondary)");
    });

    it("draws the processing state as a chip rather than an icon", () => {
        // A value, not a presence: there is no useful icon for "processed".
        const container = renderIndicator("loom:state");

        expect(container.querySelector(".MuiChip-label")?.textContent).toBe(
            "processed",
        );
        expect(iconTitles(container)).toEqual([]);
    });
});
