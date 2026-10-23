import { configureStore } from "@reduxjs/toolkit";
import { render } from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it, vi } from "vitest";

import commonReducer from "@app/slices/commonSlice";
import searchReducer, {
    openFileTab,
    setHighlightedFileId,
} from "@app/slices/searchSlice";

import { FileDetailView } from "./FileDetailView";

vi.mock("@app/tours/useTour", () => ({
    useTour: () => ({
        activeTourStepId: null,
        isTourActive: false,
        tourDetailFileId: null,
    }),
}));

// The panel loads a file and renders eight editors' worth of chrome; none of
// that is what this file is about.
vi.mock("@features/search/components/FileDetailPanel/FileDetailPanel", () => ({
    FileDetailPanel: ({
        fileId,
        isActive,
        tabKind,
    }: {
        fileId: string;
        isActive: boolean;
        tabKind: string;
    }) => (
        <div
            data-file-panel={fileId}
            data-active={isActive ? "true" : undefined}
            data-tab-kind={tabKind}
        />
    ),
}));

const renderView = (setUp: (dispatch: (action: unknown) => void) => void) => {
    const store = configureStore({
        reducer: { search: searchReducer, common: commonReducer },
    });
    setUp(store.dispatch);
    const { container } = render(
        <Provider store={store}>
            <FileDetailView />
        </Provider>,
    );
    return { container, store };
};

const panels = (container: HTMLElement, fileId: string) =>
    container.querySelectorAll(`[data-file-panel="${fileId}"]`);

const activePanels = (container: HTMLElement) =>
    container.querySelectorAll('[data-file-panel][data-active="true"]');

describe("FileDetailView", () => {
    it("shows the highlighted file on the following tab", () => {
        const { container } = renderView((dispatch) => {
            dispatch(setHighlightedFileId("a"));
        });

        expect(panels(container, "a")).toHaveLength(1);
        expect(activePanels(container)).toHaveLength(1);
    });

    it("mounts one panel for a file that is both highlighted and open", () => {
        // The common case after a double-click. Two panels carrying the same
        // `data-file-panel` would make every keyboard action that reaches
        // into a panel resolve it with `querySelector` non-deterministically.
        const { container } = renderView((dispatch) => {
            dispatch(setHighlightedFileId("a"));
            dispatch(openFileTab({ fileId: "a", background: true }));
        });

        expect(panels(container, "a")).toHaveLength(1);
    });

    it("draws an open tab's panel as the following tab when it stands in", () => {
        // A panel told it is a file tab runs the auto-actions - marking seen,
        // re-indexing, queueing a summary. Walking the highlight over a file
        // that happens to be open is not opening it, so the panel standing in
        // has to be the following tab in every respect, down to which sub-tab
        // it reads.
        const { container } = renderView((dispatch) => {
            dispatch(openFileTab({ fileId: "a", background: true }));
            dispatch(setHighlightedFileId("a"));
        });

        const panel = activePanels(container)[0];
        expect(panel.getAttribute("data-file-panel")).toBe("a");
        expect(panel.getAttribute("data-tab-kind")).toBe("follow");
    });

    it("keeps exactly one panel active whatever is selected", () => {
        const { container } = renderView((dispatch) => {
            dispatch(setHighlightedFileId("a"));
            dispatch(openFileTab({ fileId: "b" }));
            dispatch(openFileTab({ fileId: "c", background: true }));
        });

        expect(activePanels(container)).toHaveLength(1);
        expect(activePanels(container)[0].getAttribute("data-file-panel")).toBe(
            "b",
        );
    });

    it("draws the placeholder with nothing highlighted", () => {
        const { container } = renderView(() => {});

        expect(activePanels(container)).toHaveLength(0);
        expect(container.textContent).toContain("fileDetailEmpty");
    });
});
