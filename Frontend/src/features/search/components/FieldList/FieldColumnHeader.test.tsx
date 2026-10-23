import { render } from "@testing-library/react";
import { Provider } from "react-redux";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
    setFieldLayout,
    setPreviewFields,
    setThumbnailWidthRem,
} from "@app/slices/searchSlice";
import { store } from "@app/store";

import { FieldColumnHeader } from "./FieldColumnHeader";

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

const renderHeader = () =>
    render(
        <Provider store={store}>
            <FieldColumnHeader />
        </Provider>,
    );

describe("FieldColumnHeader", () => {
    afterEach(() => {
        store.dispatch(setPreviewFields(["content"]));
        store.dispatch(setFieldLayout("compact"));
    });

    it("names every selected column", () => {
        store.dispatch(setFieldLayout("line"));
        store.dispatch(setPreviewFields(["from", "subject", "size"]));

        const { container } = renderHeader();

        expect(container.textContent).toContain("from");
        expect(container.textContent).toContain("subject");
        expect(container.textContent).toContain("size");
    });

    it("puts a resize handle on every border but the first column's", () => {
        store.dispatch(setFieldLayout("line"));
        store.dispatch(setPreviewFields(["from", "subject", "size"]));
        store.dispatch(setThumbnailWidthRem(0));

        const { container } = renderHeader();

        // Three columns have two borders between them, and the leading edge
        // of the first is the list's own padding - nothing to drag there.
        expect(container.querySelectorAll('[role="separator"]')).toHaveLength(
            2,
        );
    });

    it("names and gives a border to the thumbnail column when the list reserves one", () => {
        store.dispatch(setFieldLayout("line"));
        store.dispatch(setPreviewFields(["from", "subject"]));
        store.dispatch(setThumbnailWidthRem(16));

        const { container } = renderHeader();

        expect(container.textContent).toContain(
            "generalSearchView.thumbnailColumn",
        );
        // One between the two fields, one on the thumbnail column.
        expect(container.querySelectorAll('[role="separator"]')).toHaveLength(
            2,
        );
    });
});
