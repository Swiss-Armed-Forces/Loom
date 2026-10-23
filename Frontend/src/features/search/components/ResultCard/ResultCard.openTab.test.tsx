import { configureStore } from "@reduxjs/toolkit";
import { fireEvent, render } from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it, vi } from "vitest";

import commonReducer from "@app/slices/commonSlice";
import { type SearchFileEntry } from "@app/slices/searchFileEntry";
import searchReducer, { RightSidebarTab } from "@app/slices/searchSlice";

import { ResultCard } from "./ResultCard";

vi.mock("@features/common/urls", () => ({
    webApiGetFileThumbnail: () => "about:blank",
}));

const FILE_ID = "f-1";

const searchDefaults = searchReducer(undefined, { type: "@@INIT" });

const fileEntry = {
    meta: { fileId: FILE_ID, sortFieldValue: "1" },
    preview: {
        fileId: FILE_ID,
        name: "a.txt",
        path: "/a.txt",
        tags: [],
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
        fields: { content: { value: "hello" } },
    },
} as unknown as SearchFileEntry;

const renderCard = () => {
    const store = configureStore({
        reducer: { search: searchReducer, common: commonReducer },
        preloadedState: {
            search: { ...searchDefaults, files: { [FILE_ID]: fileEntry } },
        },
    });
    render(
        <Provider store={store}>
            <ResultCard fileId={FILE_ID} />
        </Provider>,
    );
    return store;
};

const state = (store: ReturnType<typeof renderCard>) => store.getState().search;

/** The card's own body — the element its click and double-click are on. */
const card = () => document.querySelector(".resultCardParent") as HTMLElement;

describe("opening a file from a result card", () => {
    it("opens a tab and reveals the sidebar on double click", () => {
        // The headline gesture. The tabs live in the File Detail sidebar, so
        // opening one has to open the sidebar or nothing happens on screen.
        const store = renderCard();

        fireEvent.doubleClick(card());

        expect(state(store).openFileTabs).toHaveLength(1);
        expect(state(store).fileDetailSelection).toEqual({
            kind: "file",
            fileId: FILE_ID,
        });
        expect(state(store).rightSidebarTab).toBe(RightSidebarTab.FILE_DETAIL);
    });

    it("only moves the highlight on a single click", () => {
        const store = renderCard();

        fireEvent.click(card());

        expect(state(store).highlightedFileId).toBe(FILE_ID);
        expect(state(store).openFileTabs).toEqual([]);
        expect(state(store).rightSidebarTab).toBeNull();
    });

    it("leaves the selection alone on a Ctrl-click", () => {
        // A background open: the tab appears in the strip without taking the
        // reader off what they were looking at.
        const store = renderCard();

        fireEvent.click(card(), { ctrlKey: true });

        expect(state(store).openFileTabs).toHaveLength(1);
        expect(state(store).fileDetailSelection).toEqual({ kind: "follow" });
        expect(state(store).rightSidebarTab).toBe(RightSidebarTab.FILE_DETAIL);
    });
});
