import { configureStore } from "@reduxjs/toolkit";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it, vi } from "vitest";

import commonReducer from "@app/slices/commonSlice";
import { type SearchFileEntry } from "@app/slices/searchFileEntry";
import searchReducer from "@app/slices/searchSlice";

import { ResultCard } from "./ResultCard";

vi.mock("@features/common/urls", () => ({
    webApiGetFileThumbnail: () => "about:blank",
}));

const FILE_ID = "f-1";

// Spread over the slice's own defaults rather than hand-written: the reducers
// this renders through read fields well beyond the ones named here.
const searchDefaults = searchReducer(undefined, { type: "@@INIT" });

const fileEntry = {
    meta: { fileId: FILE_ID, sortFieldValue: "1" },
    preview: {
        fileId: FILE_ID,
        name: "a.txt",
        path: "/a.txt",
        tags: ["one"],
        flagged: false,
        hidden: false,
        seen: true,
        state: "processed",
        mimeType: "text/plain",
        mimeTypeGroup: "text",
        fileExtension: ".txt",
        attachmentsTotalCount: 0,
        contentIsTruncated: false,
        attachmentsSkipped: false,
        isSpam: false,
        thumbnailFileId: "thumb.png",
        fields: { content: { value: "hello" } },
    },
} as unknown as SearchFileEntry;

const storeWith = () =>
    configureStore({
        reducer: { search: searchReducer, common: commonReducer },
        preloadedState: {
            search: { ...searchDefaults, files: { [FILE_ID]: fileEntry } },
        },
    });

const renderCard = (isHighlighted: boolean) => {
    const store = storeWith();
    const { container } = render(
        <Provider store={store}>
            <ResultCard fileId={FILE_ID} isHighlighted={isHighlighted} />
        </Provider>,
    );
    return container;
};

/** The parts of the card that take up room, as a comparable shape. */
const visibleShape = (container: HTMLElement) =>
    [...container.querySelectorAll("[data-tour], img")]
        .filter((el) => !el.closest(".MuiCardHeader-action"))
        .map((el) => el.getAttribute("data-tour") ?? el.tagName)
        .sort()
        .join(",");

describe("ResultCard under the highlight", () => {
    it("draws the same elements highlighted as not", () => {
        // The highlighted card used to switch extra fields on, which made it
        // taller than the slot the list had already measured for it.
        expect(visibleShape(renderCard(true))).toBe(
            visibleShape(renderCard(false)),
        );
    });

    it("keeps the action buttons reachable but out of the layout", () => {
        // A dozen shortcuts find the highlighted card in the document and
        // click a button inside it, so the buttons have to be there — but
        // taking up room is what changed the card's height.
        const container = renderCard(true);
        expect(screen.getByLabelText("seen")).toBeTruthy();
        const actions = container.querySelector(".MuiCardHeader-action");
        expect(actions && getComputedStyle(actions).display).toBe("none");
    });
});
