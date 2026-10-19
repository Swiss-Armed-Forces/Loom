import { configureStore } from "@reduxjs/toolkit";
import { render } from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it, vi } from "vitest";

import { GetFilePreviewResponse } from "@app/api";
import commonReducer from "@app/slices/commonSlice";
import searchReducer, {
    fetchPreview,
    setShowThumbnails,
} from "@app/slices/searchSlice";

import { ResultCard } from "./ResultCard";

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

const FILE_ID = "f1";

const FILE_PREVIEW: GetFilePreviewResponse = {
    fileId: FILE_ID,
    flagged: false,
    hidden: false,
    seen: false,
    contentIsTruncated: false,
    name: "scan.pdf",
    path: "/Scans/scan.pdf",
    fileExtension: "pdf",
    state: "indexed",
    thumbnailFileId: "t1",
    fields: {
        content: { value: "Dear Bob, please find" },
    },
};

const storeShowingThumbnails = (showThumbnails: boolean) => {
    const store = configureStore({
        reducer: { search: searchReducer, common: commonReducer },
    });
    store.dispatch(setShowThumbnails(showThumbnails));
    store.dispatch({
        type: fetchPreview.fulfilled.type,
        payload: {
            query: null,
            preview: FILE_PREVIEW,
            fields: ["content"],
        },
    });
    return store;
};

/** The wrapper that holds the image's room. CSS modules keep the name. */
const reserve = (container: HTMLElement) =>
    container.querySelector('[class*="thumbnailReserve"]');

/**
 * A card that draws a thumbnail only because it is highlighted is asking for
 * that image now, not showing one it already had — so the room has to be held
 * before it arrives, or the card grows under the reader as it lands.
 */
describe("ResultCard with a thumbnail it is fetching right now", () => {
    it("holds the image's room when only the highlight shows one", () => {
        const { container } = render(
            <Provider store={storeShowingThumbnails(false)}>
                <ResultCard fileId={FILE_ID} isHighlighted />
            </Provider>,
        );

        expect(reserve(container)).not.toBeNull();
        expect(reserve(container)?.querySelector("img")).not.toBeNull();
    });

    // With thumbnails on for the list, this card's image was requested with
    // every other card's, long before the highlight arrived. Holding room for
    // one already in hand would only add a gap under a short image.
    it("holds no room when the whole list shows thumbnails", () => {
        const { container } = render(
            <Provider store={storeShowingThumbnails(true)}>
                <ResultCard fileId={FILE_ID} isHighlighted />
            </Provider>,
        );

        expect(container.querySelector("img")).not.toBeNull();
        expect(reserve(container)).toBeNull();
    });
});
