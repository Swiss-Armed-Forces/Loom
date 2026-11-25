import { configureStore, Middleware } from "@reduxjs/toolkit";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { beforeEach, describe, expect, it, vi } from "vitest";

import commonReducer from "@app/slices/commonSlice";
import searchReducer, {
    setExpandFilePaths,
    updateQuery,
} from "@app/slices/searchSlice";
import { store } from "@app/store";

import { ClickableFilePath } from "./ClickableFilePath";

// The search thunk opens a point in time over the network before it looks at
// the query it was handed. With nothing to open it returns straight away, so
// the query a click asks for is readable off the pending action alone.
vi.mock("@app/api/index", async (importOriginal) => ({
    ...(await importOriginal<typeof import("@app/api/index")>()),
    getLongRunningQuery: vi.fn(),
}));

const DEEP_PATH = "/Crawler/Imports/archive.zip/testarchive/testfile01.txt";
const SHALLOW_PATH = "/Mail/Inbox/basic_email.eml";
// Nine segments plus the toggle is ten children, past MUI's own default cap.
const VERY_DEEP_PATH = "/Crawler/Imports/a/b/c/d/e/f/testfile01.txt";

const renderPath = (fullPath: string) =>
    render(
        <Provider store={store}>
            <ClickableFilePath fullPath={fullPath} />
        </Provider>,
    );

/** A store holding `query`, rendering `SHALLOW_PATH`, and recording every
 *  query a crumb click asks for. */
const queriesAskedFrom = (query: string) => {
    const asked: string[] = [];
    const record: Middleware = () => (next) => (action) => {
        if (updateQuery.pending.match(action)) {
            asked.push(action.meta.arg.query ?? "");
        }
        return next(action);
    };
    const queryStore = configureStore({
        reducer: { search: searchReducer, common: commonReducer },
        middleware: (getDefault) => getDefault().concat(record),
    });
    queryStore.dispatch({
        type: "updateQueryThunk/fulfilled",
        payload: {
            query: {
                id: "pit-1",
                query,
                keepAlive: null,
                sortField: null,
                sortDirection: null,
                sortId: null,
                pageSize: null,
            },
            files: [],
            totalFiles: 0,
        },
    });
    render(
        <Provider store={queryStore}>
            <ClickableFilePath fullPath={SHALLOW_PATH} />
        </Provider>,
    );
    return asked;
};

const trail = () => screen.getByRole("list").textContent;
// The breadcrumb segments render as links, so the toggle is the only button
// inside the trail.
const toggle = () => screen.getByRole("button");

describe("ClickableFilePath", () => {
    beforeEach(() => {
        store.dispatch(setExpandFilePaths(false));
    });

    it("heads the trail with the toggle, ahead of the visible tail", () => {
        renderPath(DEEP_PATH);

        // The toggle sits inside the trail with a separator after it - that
        // is what signals the path continues to the left.
        expect(trail()).toBe("/archive.zip/testarchive/testfile01.txt");
        expect(toggle()).toBeInTheDocument();
    });

    it("shows the whole path once expanded", () => {
        store.dispatch(setExpandFilePaths(true));
        renderPath(DEEP_PATH);

        expect(trail()).toBe(
            "/Crawler/Imports/archive.zip/testarchive/testfile01.txt",
        );
    });

    it("lets MUI collapse no long path of its own accord", () => {
        store.dispatch(setExpandFilePaths(true));
        renderPath(VERY_DEEP_PATH);

        // Left to its default cap, MUI folded the expanded trail back to the
        // toggle and the filename and grew a second ellipsis beside ours.
        expect(trail()).toBe("/Crawler/Imports/a/b/c/d/e/f/testfile01.txt");
        expect(screen.queryByRole("button", { name: "Show path" })).toBeNull();
    });

    it("keeps the toggle heading the trail in both states", () => {
        const headsTheTrail = () =>
            screen.getByRole("list").firstChild?.contains(toggle());

        renderPath(DEEP_PATH);
        expect(headsTheTrail()).toBe(true);

        fireEvent.click(toggle());

        // Toggling swaps the icon but never moves the control, so the row
        // does not reflow under the pointer.
        expect(trail()).toContain("Crawler");
        expect(headsTheTrail()).toBe(true);
    });

    it("leaves short paths untouched, with no toggle at all", () => {
        renderPath(SHALLOW_PATH);

        expect(trail()).toBe("Mail/Inbox/basic_email.eml");
        expect(screen.queryByRole("button")).toBeNull();
    });

    it("expands every card from one click, not just its own", () => {
        renderPath(DEEP_PATH);
        fireEvent.click(toggle());

        expect(store.getState().search.expandFilePaths).toBe(true);
    });

    it("lets the row and the trail be squeezed below the path's width", () => {
        // Both are flex items whose automatic minimum size is the whole
        // unbroken path, and a trail that cannot be squeezed is laid out at
        // its full length and clipped mid-word by the header's
        // `overflow: hidden`. jsdom lays nothing out, so the floor itself is
        // what there is to assert.
        const { container } = renderPath(DEEP_PATH);
        const row = container.firstElementChild!;
        const trailRoot = screen.getByRole("list").parentElement!;

        expect(getComputedStyle(row).minWidth).toBe("0px");
        expect(getComputedStyle(trailRoot).minWidth).toBe("0px");
    });

    it("filters the file and what is indexed below it", async () => {
        // The folder view's subtree chips leave a file out of their own count
        // with a negated exact path, which this filter supersedes too.
        const asked = queriesAskedFrom(
            'parent_path:"//Mail/Inbox" NOT full_path.keyword:"//Mail/Inbox/basic_email.eml"',
        );

        await act(async () => {
            fireEvent.click(screen.getByText("basic_email"));
        });

        // The crumb reads "basic_email", the filter is the whole path on the
        // path-hierarchy field, so the file's attachments come with it - and
        // the directory filter it supersedes is gone.
        expect(asked).toEqual([
            'full_path.tree:"//Mail/Inbox/basic_email.eml"',
        ]);
    });

    it("drops the file filter when a parent crumb is clicked", async () => {
        const asked = queriesAskedFrom(
            'full_path.tree:"//Mail/Inbox/basic_email.eml"',
        );

        await act(async () => {
            fireEvent.click(screen.getByText("Inbox"));
        });

        expect(asked).toEqual(['parent_path:"//Mail/Inbox"']);
    });

    it("reaches no ancestor handler, by click or by focus", () => {
        // The result card highlights itself from both events, and a highlight
        // mid-click re-renders the row and swallows the click.
        const onClick = vi.fn();
        const onFocus = vi.fn();

        render(
            <div onClick={onClick} onFocus={onFocus}>
                <Provider store={store}>
                    <ClickableFilePath fullPath={DEEP_PATH} />
                </Provider>
            </div>,
        );

        fireEvent.focus(toggle());
        fireEvent.click(toggle());

        expect(onFocus).not.toHaveBeenCalled();
        expect(onClick).not.toHaveBeenCalled();
        expect(store.getState().search.expandFilePaths).toBe(true);
    });
});
