import { configureStore } from "@reduxjs/toolkit";
import { renderHook } from "@testing-library/react";
import { ReactNode } from "react";
import { Provider } from "react-redux";
import { describe, expect, it } from "vitest";

import commonReducer from "@app/slices/commonSlice";
import searchReducer, { setHighlightedFileId } from "@app/slices/searchSlice";

import { useKeyboardNavigation } from "./useKeyboardNavigation";

const mountWithHighlight = (fileId: string | null) => {
    const store = configureStore({
        reducer: { search: searchReducer, common: commonReducer },
    });
    store.dispatch(setHighlightedFileId(fileId));
    const wrapper = ({ children }: { children: ReactNode }) => (
        <Provider store={store}>{children}</Provider>
    );
    renderHook(() => useKeyboardNavigation(), { wrapper });
    return store;
};

/** The default binding of `scrollToHighlight`, on the document the hook binds. */
const pressScrollToHighlight = () => {
    document.dispatchEvent(
        new KeyboardEvent("keydown", {
            key: "z",
            bubbles: true,
            cancelable: true,
        }),
    );
};

describe("scrollToHighlight", () => {
    it("asks for a top-aligned scroll and leaves the highlight alone", () => {
        const store = mountWithHighlight("f-1");
        const before = store.getState().search.highlightScrollRequest;

        pressScrollToHighlight();
        pressScrollToHighlight();

        const state = store.getState().search;
        // The request is a counter, so the second press scrolls again rather
        // than being folded into the first - which is the whole point of a key
        // pressed to check where the card went.
        expect(state.highlightScrollRequest).toBe(before + 2);
        expect(state.highlightScrollMode).toBe("top");
        expect(state.highlightedFileId).toBe("f-1");
    });

    it("does nothing when nothing is highlighted", () => {
        const store = mountWithHighlight(null);
        const before = store.getState().search.highlightScrollRequest;

        pressScrollToHighlight();

        expect(store.getState().search.highlightScrollRequest).toBe(before);
    });
});
