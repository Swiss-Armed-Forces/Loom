import { configureStore } from "@reduxjs/toolkit";
import { render } from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it, vi } from "vitest";

import { GetFilePreviewResponse } from "@app/api";
import commonReducer from "@app/slices/commonSlice";
import searchReducer from "@app/slices/searchSlice";

import { FileCardHeader } from "./FileCardHeader";

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

const FILE_PREVIEW: GetFilePreviewResponse = {
    fileId: "f1",
    flagged: false,
    hidden: false,
    seen: false,
    contentIsTruncated: false,
    name: "scan.pdf",
    path: "/Scans/scan.pdf",
    fileExtension: "pdf",
    state: "indexed",
    fields: { content: { value: "Dear Bob, please find" } },
};

/**
 * Both callers pass `compact`, so it cannot be what tells them apart.
 *
 * `compact` is a statement about width - the detail panel is a narrow pane
 * and wants the tighter layout. `denseChrome` is a statement about what the
 * header *is*: one row of a long list, which can spare neither a full-size
 * icon nor a permanent action cluster. Conflating the two is what left the
 * detail panel looking empty.
 */
const renderHeader = (denseChrome: boolean) =>
    render(
        <Provider
            store={configureStore({
                reducer: { search: searchReducer, common: commonReducer },
            })}
        >
            <FileCardHeader
                filePreview={FILE_PREVIEW}
                compact
                denseChrome={denseChrome}
            />
        </Provider>,
    );

const buttonOpacity = (container: HTMLElement, selector: string) => {
    const button = container.querySelector(`.MuiCardHeader-action ${selector}`);
    if (!button) return null;
    return getComputedStyle(button).opacity;
};

const avatarSize = (container: HTMLElement) =>
    getComputedStyle(
        container.querySelector(".MuiCardHeader-avatar .MuiAvatar-root")!,
    ).width;

describe("FileCardHeader dressed as a dense row", () => {
    it("hides the actions until the row is hovered, bar the overflow menu", () => {
        const { container } = renderHeader(true);

        expect(container.querySelector(".MuiCardHeader-action")).not.toBeNull();
        expect(
            buttonOpacity(container, "button:not([data-always-visible])"),
        ).toBe("0");
        // A card that showed nothing at all until the pointer reached it gave
        // a reader no reason to think there were actions to go looking for.
        expect(
            buttonOpacity(container, "button[data-always-visible]"),
        ).not.toBe("0");
    });

    it("shrinks the icon to what a list row can spare", () => {
        expect(avatarSize(renderHeader(true).container)).toBe("24px");
    });
});

describe("FileCardHeader in a narrow pane that is not a list", () => {
    // The regression: the detail panel is compact, so it was given the dense
    // dressing too, and its actions became invisible.
    it("shows its actions", () => {
        const { container } = renderHeader(false);

        expect(
            container.querySelectorAll(".MuiCardHeader-action button").length,
        ).toBeGreaterThan(0);
        expect(buttonOpacity(container, "button")).not.toBe("0");
    });

    it("keeps its icon full size", () => {
        expect(avatarSize(renderHeader(false).container)).not.toBe("24px");
    });
});
