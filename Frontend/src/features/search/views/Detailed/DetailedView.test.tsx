import { configureStore } from "@reduxjs/toolkit";
import { render, screen } from "@testing-library/react";
import { useRef } from "react";
import { Provider } from "react-redux";
import { beforeAll, describe, expect, it, vi } from "vitest";

import commonReducer from "@app/slices/commonSlice";
import searchReducer, { searchSlice } from "@app/slices/searchSlice";
import { SearchPanelContext } from "@features/search/views/SearchResults/SearchPanelContext";

import { DetailedView } from "./DetailedView";

// The cards themselves are not under test here and pull in half the app, so
// they are stood in for by something with a height.
vi.mock("@features/search/components", () => ({
    ResultCard: ({ fileId }: { fileId: string }) => (
        <div data-testid="result-card" data-file-id={fileId} />
    ),
    LoadMoreButton: () => <div data-testid="load-more" />,
    EmptySearchResults: () => <div data-testid="empty" />,
}));

const VIEWPORT_HEIGHT = 800;
const ROW_HEIGHT = 200;

/**
 * Give jsdom enough of a layout for the virtualizer to work in.
 *
 * jsdom has no layout engine, so every element measures zero and the
 * virtualizer would conclude that nothing is visible. Rows report a fixed
 * height and the scroller a fixed viewport; nothing else here depends on the
 * exact numbers, only on the viewport holding a handful of rows rather than
 * all of them.
 */
const isScroller = (el: HTMLElement) => el.dataset.searchPanel !== undefined;
const heightOf = (el: HTMLElement) =>
    isScroller(el) ? VIEWPORT_HEIGHT : ROW_HEIGHT;

beforeAll(() => {
    for (const prop of ["clientHeight", "offsetHeight"] as const) {
        Object.defineProperty(HTMLElement.prototype, prop, {
            configurable: true,
            get(this: HTMLElement) {
                return heightOf(this);
            },
        });
    }
    // `offsetHeight` above is the one that matters: it is what the
    // virtualizer's default measureElement falls back to when there is no
    // ResizeObserver entry, which is every measurement here. Left at jsdom's
    // zero, every row measures empty and the virtualizer re-measures forever.
    HTMLElement.prototype.getBoundingClientRect = function (this: HTMLElement) {
        const height = heightOf(this);
        return {
            top: 0,
            left: 0,
            width: 1_200,
            height,
            bottom: height,
            right: 1_200,
            x: 0,
            y: 0,
            toJSON: () => ({}),
        } as DOMRect;
    };
});

const storeWith = (resultCount: number) => {
    const store = configureStore({
        reducer: { search: searchReducer, common: commonReducer },
    });
    store.dispatch({
        type: "updateQueryThunk/fulfilled",
        payload: {
            query: {
                id: "pit-1",
                query: "foo",
                keepAlive: null,
                sortField: null,
                sortDirection: null,
                sortId: null,
                pageSize: null,
            },
            files: Array.from({ length: resultCount }, (_, i) => ({
                fileId: `f-${i}`,
                sortId: [i],
            })),
            totalFiles: resultCount,
        },
    });
    return store;
};

const Harness = ({ store }: { store: ReturnType<typeof storeWith> }) => {
    const scrollRef = useRef<HTMLDivElement>(null);
    return (
        <Provider store={store}>
            <div data-search-panel ref={scrollRef}>
                <SearchPanelContext.Provider value={{ scrollRef }}>
                    <DetailedView />
                </SearchPanelContext.Provider>
            </div>
        </Provider>
    );
};

describe("DetailedView", () => {
    it("renders a window of cards, not the whole result list", () => {
        render(<Harness store={storeWith(500)} />);

        const cards = screen.getAllByTestId("result-card");
        // The whole point: 500 loaded results must not be 500 mounted cards.
        // The exact count is viewport plus overscan, so this asserts the order
        // of magnitude rather than pinning the tuning.
        expect(cards.length).toBeGreaterThan(0);
        expect(cards.length).toBeLessThan(40);
    });

    it("starts at the top of the result order", () => {
        render(<Harness store={storeWith(500)} />);

        expect(screen.getAllByTestId("result-card")[0]).toHaveAttribute(
            "data-file-id",
            "f-0",
        );
    });

    // The list is sized for everything loaded even though only a window is
    // rendered, or the scrollbar would describe the window instead.
    it("reserves the height of the whole list", () => {
        render(<Harness store={storeWith(500)} />);

        const list = screen.getByTestId("virtual-list");
        const height = Number.parseInt(list.style.height, 10);
        expect(height).toBeGreaterThan(500 * ROW_HEIGHT * 0.5);
    });

    it("keeps the highlighted card rendered when it is far off screen", () => {
        const store = storeWith(500);
        store.dispatch(searchSlice.actions.setHighlightedFileId("f-400"));

        render(<Harness store={store} />);

        // Roughly a dozen hotkeys find the highlighted card with
        // document.querySelector and click a button inside it, so it has to
        // stay in the DOM however far the list has scrolled away from it.
        const ids = screen
            .getAllByTestId("result-card")
            .map((el) => el.getAttribute("data-file-id"));

        expect(ids).toContain("f-400");
        // Still a window, not the whole list up to it.
        expect(ids.length).toBeLessThan(40);
    });

    it("shows the empty state with no results", () => {
        render(<Harness store={storeWith(0)} />);

        expect(screen.getByTestId("empty")).toBeInTheDocument();
    });
});
