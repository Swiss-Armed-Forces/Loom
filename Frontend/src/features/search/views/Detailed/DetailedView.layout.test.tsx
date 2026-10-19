import { configureStore } from "@reduxjs/toolkit";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { useRef } from "react";
import { Provider } from "react-redux";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import commonReducer from "@app/slices/commonSlice";
import searchReducer, {
    bumpHighlightScroll,
    FieldLayout,
    NamedDensity,
    setCardDensity,
    setFieldLayout,
    setHighlightedFileId,
} from "@app/slices/searchSlice";
import { SearchPanelContext } from "@features/search/components/CenterTabs/SearchPanelContext";

import { DetailedView } from "./DetailedView";

vi.mock("@features/search/components", () => ({
    ResultCard: ({ fileId }: { fileId: string }) => (
        <div data-testid="result-card" data-file-id={fileId} />
    ),
    LoadMoreButton: () => <div data-testid="load-more" />,
    EmptySearchResults: () => <div data-testid="empty" />,
}));

const VIEWPORT_HEIGHT = 800;

/**
 * How tall a card is in each field layout.
 *
 * The point of this file: the layouts really do render cards of different
 * heights, so a measurement taken under one of them is wrong under the next.
 */
const ROW_HEIGHT: Record<FieldLayout, number> = {
    rows: 240,
    compact: 120,
    line: 48,
};

let currentLayout: FieldLayout = "rows";
let currentSpacing: NamedDensity = "standard";

/**
 * How tall a card is at each spacing.
 *
 * Tighter spacing trims padding and line height; it does not remove any
 * fields, so even the tightest card is nothing like as short as an empty one.
 * Getting this wrong in the estimate is what puts rows on top of each other.
 */
const SPACING_HEIGHT: Record<NamedDensity, number> = {
    compact: 180,
    standard: 260,
    full: 400,
};

/**
 * A ResizeObserver the test can fire, standing in for the browser's.
 *
 * The global stub in `src/test/setup.ts` is inert, which would hide the
 * behaviour under test entirely: a row that stays mounted across a settings
 * change is never handed back to React's ref, so its ResizeObserver is the
 * only thing that can re-measure it.
 */
const observers: {
    cb: ResizeObserverCallback;
    targets: Set<Element>;
    self: ResizeObserver;
}[] = [];

class FakeResizeObserver implements ResizeObserver {
    private targets = new Set<Element>();
    constructor(cb: ResizeObserverCallback) {
        observers.push({ cb, targets: this.targets, self: this });
    }
    observe(target: Element) {
        this.targets.add(target);
    }
    unobserve(target: Element) {
        this.targets.delete(target);
    }
    disconnect() {
        this.targets.clear();
    }
}

const flushResizeObservers = () => {
    for (const { cb, targets, self } of observers) {
        const entries = [...targets].map(
            (target) =>
                ({
                    target,
                    borderBoxSize: [
                        {
                            blockSize: (target as HTMLElement).offsetHeight,
                            inlineSize: 1_200,
                        },
                    ],
                    contentRect: {
                        width: 1_200,
                        height: (target as HTMLElement).offsetHeight,
                    },
                }) as unknown as ResizeObserverEntry,
        );
        if (entries.length) cb(entries, self);
    }
};

const isScroller = (el: HTMLElement) => el.dataset.searchPanel !== undefined;
const isRow = (el: HTMLElement) => el.dataset.index !== undefined;

/**
 * Rows whose preview has arrived since they were placed.
 *
 * Walking the list quickly lands on cards that have not loaded yet, so what
 * gets measured is a skeleton and what ends up there is several times taller
 * — most of all the highlighted one, which shows every element.
 */
const grownRows = new Set<number>();

/** How much taller a card is once it has something to show. */
const GROWTH = 220;

/**
 * Cards are not all the same height — they hold different amounts of content
 * — and a uniform stand-in would hide exactly the errors this is looking for,
 * since every wrong guess would happen to be the right answer.
 */
const rowHeight = (index: number) =>
    (currentLayout === "rows"
        ? SPACING_HEIGHT[currentSpacing]
        : ROW_HEIGHT[currentLayout]) +
    (index % 5) * 17 +
    (grownRows.has(index) ? GROWTH : 0);

const heightOf = (el: HTMLElement) => {
    if (isScroller(el)) return VIEWPORT_HEIGHT;
    if (isRow(el)) return rowHeight(Number(el.dataset.index));
    return 0;
};

/** Every scroll the virtualizer writes, in order; jsdom implements none. */
const scrollWrites: number[] = [];

beforeAll(() => {
    vi.stubGlobal("ResizeObserver", FakeResizeObserver);
    HTMLElement.prototype.scrollTo = ((options: ScrollToOptions) => {
        scrollWrites.push(options.top ?? 0);
    }) as HTMLElement["scrollTo"];
    for (const prop of ["clientHeight", "offsetHeight"] as const) {
        Object.defineProperty(HTMLElement.prototype, prop, {
            configurable: true,
            get(this: HTMLElement) {
                return heightOf(this);
            },
        });
    }
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

beforeEach(() => {
    observers.length = 0;
    scrollWrites.length = 0;
    grownRows.clear();
    currentLayout = "rows";
    currentSpacing = "standard";
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
            <div data-search-panel data-testid="search-panel" ref={scrollRef}>
                <SearchPanelContext.Provider
                    value={{ scrollRef, isActive: true }}
                >
                    <DetailedView />
                </SearchPanelContext.Provider>
            </div>
        </Provider>
    );
};

/** Each rendered row's index and the offset it was placed at. */
const placedRows = () =>
    screen
        .getAllByTestId("result-card")
        .map((card) => card.parentElement as HTMLElement)
        .map((row) => ({
            index: Number(row.dataset.index),
            offset: Number(
                /translateY\((-?[\d.]+)px\)/.exec(row.style.transform)?.[1] ??
                    NaN,
            ),
        }))
        .sort((a, b) => a.index - b.index);

/** The tightest spacing between consecutive rows; negative is an overlap. */
const worstSlack = () => {
    const rows = placedRows();
    let worst = Infinity;
    for (let i = 1; i < rows.length; i++) {
        if (rows[i].index !== rows[i - 1].index + 1) continue;
        // Slack: how much room the previous row was given beyond what it
        // needs. Negative means the two are drawn on top of each other.
        worst = Math.min(
            worst,
            rows[i].offset - rows[i - 1].offset - rowHeight(rows[i - 1].index),
        );
    }
    return worst;
};

describe("DetailedView under a layout change", () => {
    it("does not overlap rows when the field layout resizes every card", () => {
        const store = storeWith(500);
        render(<Harness store={store} />);
        act(() => flushResizeObservers());

        expect(worstSlack()).toBeGreaterThanOrEqual(0);

        // The cards really do get shorter, the way they do in the browser.
        act(() => {
            currentLayout = "compact";
            store.dispatch(setFieldLayout("compact"));
        });
        act(() => flushResizeObservers());

        expect(worstSlack()).toBeGreaterThanOrEqual(0);
    });

    // The browser delivers resize notifications after the frame, so what the
    // user sees first is whatever the list drew without them. A row that was
    // already mounted is never handed back to React's ref, so this is its
    // only correction — and the frame before it arrives is the one that shows
    // cards on top of each other.
    it("does not overlap before the resize notifications arrive", () => {
        const store = storeWith(500);
        render(<Harness store={store} />);
        act(() => flushResizeObservers());

        act(() => {
            currentLayout = "compact";
            store.dispatch(setFieldLayout("compact"));
        });

        expect(worstSlack()).toBeGreaterThanOrEqual(0);
    });

    // The reported case: everything on screen at the loosest spacing, then
    // switched to the tightest.
    it("does not overlap when the spacing is tightened", async () => {
        const store = storeWith(500);
        currentSpacing = "full";
        store.dispatch(setCardDensity("full"));
        render(<Harness store={store} />);
        act(() => flushResizeObservers());

        expect(worstSlack()).toBeGreaterThanOrEqual(0);

        // Awaited because the rows are re-read in a microtask: reporting a
        // height makes the virtualizer notify, and its React adapter answers
        // a synchronous notification with `flushSync`, which React refuses
        // from inside a commit. The microtask still runs before the browser
        // paints, so the guarantee is the first frame, not the commit.
        await act(async () => {
            currentSpacing = "compact";
            store.dispatch(setCardDensity("compact"));
        });

        expect(worstSlack()).toBeGreaterThanOrEqual(0);
    });

    // The reserved height is what the scrollbar describes. Every measured
    // height is cached against its row, so a settings change that resizes the
    // cards leaves the cache quoting a layout that is gone — and the list
    // would go on reserving room for cards nobody is looking at any more.
    it("reserves a height that follows the new card height", () => {
        const store = storeWith(500);
        render(<Harness store={store} />);
        act(() => flushResizeObservers());
        const reserved = () =>
            Number.parseInt(
                screen.getByTestId("virtual-list").style.height,
                10,
            );

        const before = reserved();

        act(() => {
            currentLayout = "line";
            store.dispatch(setFieldLayout("line"));
        });
        act(() => flushResizeObservers());

        // One line per card where the stacked layout drew several.
        expect(reserved()).toBeLessThan(before / 2);
    });

    it("does not overlap rows when the cards get taller", () => {
        const store = storeWith(500);
        currentLayout = "line";
        store.dispatch(setFieldLayout("line"));
        render(<Harness store={store} />);
        act(() => flushResizeObservers());

        expect(worstSlack()).toBeGreaterThanOrEqual(0);

        act(() => {
            currentLayout = "rows";
            store.dispatch(setFieldLayout("rows"));
        });
        act(() => flushResizeObservers());

        expect(worstSlack()).toBeGreaterThanOrEqual(0);
    });
});

/**
 * Placing the highlighted card is not something that can be done once.
 *
 * Walking the list quickly lands on cards whose preview has not arrived, so
 * the card the list places is a skeleton and the card that ends up there is
 * several times taller — and the scroll position that was right for the one
 * leaves the other hanging off the bottom of the viewport.
 */
describe("DetailedView when the highlighted card turns out taller", () => {
    const placeFarDownTheList = () => {
        const store = storeWith(500);
        store.dispatch(setHighlightedFileId("f-40"));
        store.dispatch(bumpHighlightScroll("smart"));
        render(<Harness store={store} />);
        act(() => flushResizeObservers());
        return store;
    };

    // Only that the card is placed again, not where: jsdom reports no
    // scrollHeight, so every offset the virtualizer resolves clamps to zero.
    // Where it lands is the virtualizer's own arithmetic over heights this
    // file models rather than renders, which is not ours to assert.
    it("places it again when its preview arrives", () => {
        placeFarDownTheList();
        const placements = scrollWrites.length;
        expect(placements).toBeGreaterThan(0);

        grownRows.add(40);
        act(() => flushResizeObservers());

        expect(scrollWrites.length).toBeGreaterThan(placements);
    });

    it("leaves the scroll alone once the user has taken it over", () => {
        placeFarDownTheList();
        const placements = scrollWrites.length;

        // A wheel is the user's, and a card that grows after they have
        // scrolled away from it must not pull them back to it.
        fireEvent.wheel(screen.getByTestId("search-panel"));
        grownRows.add(40);
        act(() => flushResizeObservers());

        expect(scrollWrites.length).toBe(placements);
    });
});

/**
 * Picking a card with the mouse is not a request to move it.
 *
 * The card being pointed at is on screen by definition, and the one thing it
 * must not do is leave from under the pointer. So the keyboard, the folder
 * tree and the chat all bump `highlightScrollRequest` and a click deliberately
 * does not — `ResultCard` dispatches `setHighlightedFileId` on its own.
 */
describe("DetailedView when the mouse moves the highlight", () => {
    const settled = () => {
        const store = storeWith(500);
        render(<Harness store={store} />);
        act(() => flushResizeObservers());
        return store;
    };

    it("does not scroll a card that was clicked", () => {
        const store = settled();
        const placements = scrollWrites.length;

        // What a click is, from the list's point of view: the scroller sees
        // the mousedown, and the highlight changes without a request. Both
        // halves matter — the mousedown is what tells the correction below
        // that the user is driving.
        fireEvent.mouseDown(screen.getByTestId("search-panel"));
        act(() => {
            store.dispatch(setHighlightedFileId("f-41"));
        });

        expect(scrollWrites.length).toBe(placements);
    });

    // Without this the test above would pass just as well on a list that never
    // scrolls for anyone.
    it("still scrolls when the keyboard asks for it", () => {
        const store = settled();
        const placements = scrollWrites.length;

        act(() => {
            store.dispatch(setHighlightedFileId("f-41"));
            store.dispatch(bumpHighlightScroll("smart"));
        });

        expect(scrollWrites.length).toBeGreaterThan(placements);
    });
});
