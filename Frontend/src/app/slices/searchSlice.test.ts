import { configureStore } from "@reduxjs/toolkit";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SearchQuery } from "@features/common/utils/model";

import { RootState } from "../store";

import {
    CustomQuery,
    addCustomQuery,
    cursorKey,
    fetchFilesCountForCustomQuery,
    fetchNextPage,
    fetchPreview,
    fileInViewChanged,
    initCustomQuery,
    loadPersistedSearchState,
    normalizeCustomQueries,
    openFileTab,
    prefetchNextPage,
    queueResultAdvance,
    revealFileThunk,
    MAX_FIELD_COLUMNS,
    searchSlice,
    focusFileTab,
    closeFileTab,
    setPreviewFields,
    setPreviewFieldColumn,
    addFieldColumn,
    removeFieldColumn,
    selectBoldPreviewFields,
    selectCardElementVisibility,
    selectFilesInView,
    selectFilesInViewOrdered,
    selectHasMoreResults,
    selectCurrentResultRank,
    selectIsPaginating,
    selectLeftSidebarWidth,
    selectFieldColumnCount,
    selectFieldColumnOf,
    toggleBoldPreviewField,
    selectRightSidebarWidth,
    selectLoadedFiles,
    selectOrderedFileIds,
    selectPaginationError,
    selectTotalFiles,
    setHighlightedFileId,
    setLeftSidebarWidth,
    setRightSidebarWidth,
    setShowTags,
    setTemporaryFileId,
    visibleRangeChanged,
    updateQuery,
} from "./searchSlice";

const mockToastError = vi.hoisted(() => vi.fn());
const mockGetFile = vi.hoisted(() => vi.fn());

vi.mock("i18next", () => ({
    t: (key: string) => key,
}));

vi.mock("react-toastify", () => ({
    toast: { error: mockToastError },
}));

vi.mock("@app/api", async (importOriginal) => ({
    ...(await importOriginal<typeof import("@app/api")>()),
    getFile: mockGetFile,
}));

describe("search query cancellation", () => {
    beforeEach(() => mockToastError.mockClear());

    it("ignores an intentionally aborted query", () => {
        const initialState = searchSlice.reducer(undefined, {
            type: "test/initialize",
        });

        const nextState = searchSlice.reducer(initialState, {
            type: updateQuery.rejected.type,
            meta: { aborted: true },
            payload: "cancelled",
        });

        expect(nextState).toBe(initialState);
        expect(mockToastError).not.toHaveBeenCalled();
    });

    it("still reports a genuine query failure", () => {
        const initialState = searchSlice.reducer(undefined, {
            type: "test/initialize",
        });

        const nextState = searchSlice.reducer(initialState, {
            type: updateQuery.rejected.type,
            meta: { aborted: false },
            payload: "search failed",
        });

        expect(nextState.queryError).toBe("search failed");
        expect(mockToastError).toHaveBeenCalledOnce();
    });
});

const SAVED_QUERY: SearchQuery = {
    id: null,
    query: "tags:interesting",
    keepAlive: null,
    sortField: null,
    sortDirection: null,
    sortId: null,
    pageSize: null,
};

const stateWith = (customQuery: CustomQuery) =>
    searchSlice.reducer(
        searchSlice.reducer(undefined, { type: "test/initialize" }),
        addCustomQuery(customQuery),
    );

const savedQuery = (overrides: Partial<CustomQuery> = {}): CustomQuery => ({
    ...initCustomQuery(SAVED_QUERY, 10, "Interesting", "Stars"),
    ...overrides,
});

const countReported = (customQueryId: string, totalFiles: number) => ({
    type: fetchFilesCountForCustomQuery.fulfilled.type,
    payload: { response: { totalFiles }, customQueryId },
});

describe("saved query new-file detection", () => {
    it("baselines a new saved query against its current count", () => {
        const customQuery = initCustomQuery(SAVED_QUERY, 7, "Q", "Stars");

        expect(customQuery.lastSeenCount).toBe(7);
        expect(customQuery.hasNewFiles).toBe(false);
    });

    it("flags new files when the count rises above the baseline", () => {
        const customQuery = savedQuery();

        const [updated] = searchSlice.reducer(
            stateWith(customQuery),
            countReported(customQuery.id, 12),
        ).customQueries;

        expect(updated.lastSeenCount).toBe(10);
        expect(updated.hasNewFiles).toBe(true);
    });

    it("clears the flag when the count matches the baseline", () => {
        const customQuery = savedQuery({
            lastSeenCount: 10,
            hasNewFiles: true,
        });

        const [updated] = searchSlice.reducer(
            stateWith(customQuery),
            countReported(customQuery.id, 10),
        ).customQueries;

        // hasNewFiles stays true because the reducer does:
        // hasNewFiles = newFileCount > lastSeenCount || hasNewFiles
        // Once true, it stays true until manually cleared elsewhere
        expect(updated.lastSeenCount).toBe(10);
        expect(updated.hasNewFiles).toBe(true);
    });

    it("keeps the flag set when the count falls below the baseline", () => {
        const customQuery = savedQuery({
            lastSeenCount: 10,
            hasNewFiles: true,
        });

        const [updated] = searchSlice.reducer(
            stateWith(customQuery),
            countReported(customQuery.id, 5),
        ).customQueries;

        expect(updated.lastSeenCount).toBe(10);
        expect(updated.hasNewFiles).toBe(true);
    });
});

describe("normalizeCustomQueries", () => {
    it("drops null and non-object entries", () => {
        expect(normalizeCustomQueries([null, 7, "string"])).toEqual([]);
    });

    it("drops objects without a query", () => {
        expect(normalizeCustomQueries([{}, { id: "no-query" }])).toEqual([]);
    });

    it("normalizes a valid entry", () => {
        const [normalized] = normalizeCustomQueries([
            {
                id: "q1",
                query: { id: null, query: "foo", keepAlive: null },
                name: "Test",
            },
        ]);

        expect(normalized).toEqual(
            expect.objectContaining({
                id: "q1",
                query: { id: null, query: "foo", keepAlive: null },
                fileCount: 0,
                lastSeenCount: 0,
                hasNewFiles: false,
                name: "Test",
            }),
        );
    });

    it("migrates legacy fileCount into lastSeenCount", () => {
        const migrated = normalizeCustomQueries([
            {
                id: "q1",
                query: { id: null, query: "foo", keepAlive: null },
                fileCount: 7,
                name: "Test",
            },
        ])[0];

        expect(migrated.fileCount).toBe(7);
        expect(migrated.lastSeenCount).toBe(7);
        expect(migrated.hasNewFiles).toBe(false);
    });

    it("preserves hasNewFiles when present", () => {
        const [migrated] = normalizeCustomQueries([
            {
                id: "q1",
                query: { id: null, query: "foo", keepAlive: null },
                fileCount: 5,
                lastSeenCount: 3,
                hasNewFiles: true,
                name: "Test",
            },
        ]);

        expect(migrated.fileCount).toBe(5);
        expect(migrated.lastSeenCount).toBe(3);
        expect(migrated.hasNewFiles).toBe(true);
    });

    it("drops malformed entries and non-array input", () => {
        expect(
            normalizeCustomQueries([null, 7, {}, { id: "no-query" }]),
        ).toEqual([]);
        expect(normalizeCustomQueries(undefined)).toEqual([]);
    });

    it("migrates saved queries while rehydrating", () => {
        window.localStorage.setItem(
            "SEARCH_STATE",
            JSON.stringify({
                expandFilePaths: true,
                customQueries: [{ ...savedQuery(), lastSeenCount: undefined }],
            }),
        );

        const persisted = loadPersistedSearchState();

        expect(persisted.expandFilePaths).toBe(true);
        expect(persisted.customQueries?.[0].lastSeenCount).toBe(10);
    });
});

type SearchStateSlice = ReturnType<typeof searchSlice.reducer>;

const emptySearchState = () =>
    searchSlice.reducer(undefined, { type: "test/initialize" });

const searchState = (search: SearchStateSlice) => ({ search }) as RootState;

const queryWithId = (id: string, query: string): SearchQuery => ({
    ...SAVED_QUERY,
    id,
    query,
});

// `startSortId` keeps a later page's search-after cursor above the previous
// page's, which is the only thing the backend can produce.
const hits = (count: number, prefix: string, startSortId = 0) =>
    Array.from({ length: count }, (_, index) => ({
        fileId: `${prefix}-${index}`,
        sortId: [startSortId + index],
    }));

// The first page of a query. The total comes from the count, which is only
// asked for here — later pages report hits alone — so it can exceed the page.
const resultsReported = (
    id: string,
    query: string,
    files: ReturnType<typeof hits>,
    totalFiles: number = files.length,
) => ({
    type: updateQuery.fulfilled.type,
    payload: { query: queryWithId(id, query), files, totalFiles },
});

// A later page. `updateQuery` only ever delivers the first page of a query;
// everything after it arrives through `fetchNextPage`. The cursor is the sort
// id of the last hit already loaded — a page reporting any other cursor belongs
// to a query the list has moved past and is dropped.
const nextPageReported = (files: ReturnType<typeof hits>, cursor: any[]) => ({
    type: fetchNextPage.fulfilled.type,
    payload: { files, cursorKey: cursorKey(cursor), fromStaged: false },
});

const previewReported = (fileId: string) => ({
    type: fetchPreview.fulfilled.type,
    payload: { query: SAVED_QUERY, preview: { fileId } },
});

// Oracle for the counter, cross-checked against the other selector instead of
// re-applying selectLoadedFiles' own predicate: selectOrderedFileIds leads with
// the temporary card when there is one, so dropping that leaves the result
// cards DetailedView renders.
// The bound holds as long as every counted card is still a hit of the reported
// total, which is the case in every scenario it is asserted in below; a stale
// card can outlive its hit, so the stale test deliberately makes no such claim.
const expectWithinTotal = (search: SearchStateSlice) =>
    expect(selectLoadedFiles(searchState(search))).toBeLessThanOrEqual(
        selectTotalFiles(searchState(search)),
    );

describe("loaded result count", () => {
    it("ignores a file kept alive by an open tab across a new query", () => {
        const firstQuery = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(5, "a")),
        );
        const withTab = searchSlice.reducer(
            firstQuery,
            openFileTab({ fileId: "a-0" }),
        );
        const secondQuery = searchSlice.reducer(
            withTab,
            resultsReported("q2", "bar", hits(3, "b")),
        );

        expect(selectLoadedFiles(searchState(secondQuery))).toBe(3);
        expectWithinTotal(secondQuery);
    });

    it("counts a file fetched after the results page it arrived in", () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const withPreview = searchSlice.reducer(
            results,
            previewReported("a-0"),
        );

        expect(selectLoadedFiles(searchState(withPreview))).toBe(3);
        expectWithinTotal(withPreview);
    });

    it("counts a file fetched before its results page arrived", () => {
        const withPreview = searchSlice.reducer(
            emptySearchState(),
            previewReported("a-0"),
        );
        const results = searchSlice.reducer(
            withPreview,
            resultsReported("q1", "foo", hits(3, "a")),
        );

        expect(selectLoadedFiles(searchState(results))).toBe(3);
        expectWithinTotal(results);
    });

    it("counts a file fetched across a query refresh", () => {
        const firstQuery = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const withPreview = searchSlice.reducer(
            firstQuery,
            previewReported("a-0"),
        );
        const refresh = searchSlice.reducer(
            withPreview,
            resultsReported("q1", "foo", hits(3, "a")),
        );

        expect(selectLoadedFiles(searchState(refresh))).toBe(3);
        expectWithinTotal(refresh);
    });

    it("counts a file fetched after its results page was superseded", () => {
        const firstQuery = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const secondQuery = searchSlice.reducer(
            firstQuery,
            resultsReported("q2", "bar", hits(3, "b")),
        );
        const withPreview = searchSlice.reducer(
            secondQuery,
            previewReported("b-0"),
        );

        expect(selectLoadedFiles(searchState(withPreview))).toBe(3);
        expectWithinTotal(withPreview);
    });

    it("counts a file fetched after its results page was superseded by a refresh", () => {
        const firstQuery = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const secondQuery = searchSlice.reducer(
            firstQuery,
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const withPreview = searchSlice.reducer(
            secondQuery,
            previewReported("a-0"),
        );

        expect(selectLoadedFiles(searchState(withPreview))).toBe(3);
        expectWithinTotal(withPreview);
    });

    // Guards against an over-correction that would count just the last page.
    // Every entry here is clean, so filtering plays no part in the total.
    it("counts every page once pagination has loaded them", () => {
        // The count runs with the first page only, so it reports the whole
        // result set up front and later pages carry no total of their own.
        const firstPage = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(12, "b"), 20),
        );

        const secondPage = searchSlice.reducer(
            firstPage,
            nextPageReported(hits(8, "c", 12), [11]),
        );

        expect(selectLoadedFiles(searchState(secondPage))).toBe(20);
        expectWithinTotal(secondPage);
    });

    it("counts a file fetched after its results page was superseded by a different query", () => {
        const firstQuery = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const secondQuery = searchSlice.reducer(
            firstQuery,
            resultsReported("q2", "bar", hits(3, "b")),
        );
        const withPreview = searchSlice.reducer(
            secondQuery,
            previewReported("b-0"),
        );
        const thirdQuery = searchSlice.reducer(
            withPreview,
            resultsReported("q3", "baz", hits(3, "c")),
        );

        expect(selectLoadedFiles(searchState(thirdQuery))).toBe(3);
        expectWithinTotal(thirdQuery);
    });

    it("counts a file fetched after its results page was superseded by a different query refresh", () => {
        const firstQuery = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const secondQuery = searchSlice.reducer(
            firstQuery,
            resultsReported("q2", "bar", hits(3, "b")),
        );
        const withPreview = searchSlice.reducer(
            secondQuery,
            previewReported("b-0"),
        );
        const thirdQuery = searchSlice.reducer(
            withPreview,
            resultsReported("q2", "bar", hits(3, "b")),
        );

        expect(selectLoadedFiles(searchState(thirdQuery))).toBe(3);
        expectWithinTotal(thirdQuery);
    });

    it("counts a file fetched after its results page was superseded by a different query page", () => {
        const firstQuery = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const secondQuery = searchSlice.reducer(
            firstQuery,
            resultsReported("q2", "bar", hits(3, "b")),
        );
        const withPreview = searchSlice.reducer(
            secondQuery,
            previewReported("b-0"),
        );
        const thirdQuery = searchSlice.reducer(
            withPreview,
            resultsReported("q3", "baz", hits(3, "c")),
        );

        expect(selectLoadedFiles(searchState(thirdQuery))).toBe(3);
        expectWithinTotal(thirdQuery);
    });

    it("counts a file fetched after its results page was superseded by a different query page refresh", () => {
        const firstQuery = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const secondQuery = searchSlice.reducer(
            firstQuery,
            resultsReported("q2", "bar", hits(3, "b")),
        );
        const withPreview = searchSlice.reducer(
            secondQuery,
            previewReported("b-0"),
        );
        const thirdQuery = searchSlice.reducer(
            withPreview,
            resultsReported("q3", "baz", hits(3, "c")),
        );

        expect(selectLoadedFiles(searchState(thirdQuery))).toBe(3);
        expectWithinTotal(thirdQuery);
    });

    it("counts a file fetched after its results page was superseded by a different query page refresh with different sort", () => {
        const firstQuery = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const secondQuery = searchSlice.reducer(
            firstQuery,
            resultsReported("q2", "bar", hits(3, "b")),
        );
        const withPreview = searchSlice.reducer(
            secondQuery,
            previewReported("b-0"),
        );
        const thirdQuery = searchSlice.reducer(
            withPreview,
            resultsReported("q3", "baz", hits(3, "c")),
        );

        expect(selectLoadedFiles(searchState(thirdQuery))).toBe(3);
        expectWithinTotal(thirdQuery);
    });

    it("counts a file fetched after its results page was superseded by a different query page refresh with different sort and different query", () => {
        const firstQuery = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "a")),
        );
        const secondQuery = searchSlice.reducer(
            firstQuery,
            resultsReported("q2", "bar", hits(3, "b")),
        );
        const withPreview = searchSlice.reducer(
            secondQuery,
            previewReported("b-0"),
        );
        const thirdQuery = searchSlice.reducer(
            withPreview,
            resultsReported("q3", "baz", hits(3, "c")),
        );

        expect(selectLoadedFiles(searchState(thirdQuery))).toBe(3);
        expectWithinTotal(thirdQuery);
    });
});

describe("result order", () => {
    const pagedTwice = () => {
        const firstPage = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "b")),
        );
        return searchSlice.reducer(
            firstPage,
            nextPageReported(hits(2, "c", 3), [2]),
        );
    };

    it("keeps pages in the order the backend ranked them", () => {
        expect(selectOrderedFileIds(searchState(pagedTwice()))).toEqual([
            "b-0",
            "b-1",
            "b-2",
            "c-0",
            "c-1",
        ]);
    });

    it("puts a returning hit at its rank, not where the cache first saw it", () => {
        const firstPage = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(2, "b")),
        );
        const cached = searchSlice.reducer(firstPage, previewReported("late"));
        const nextPage = searchSlice.reducer(
            cached,
            nextPageReported([{ fileId: "late", sortId: [2] }], [1]),
        );

        expect(selectOrderedFileIds(searchState(nextPage))).toEqual([
            "b-0",
            "b-1",
            "late",
        ]);
    });

    it("lists a hit that arrives on two pages once", () => {
        const firstPage = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(2, "b")),
        );
        const again = searchSlice.reducer(
            firstPage,
            nextPageReported([{ fileId: "b-1", sortId: [5] }], [1]),
        );

        expect(selectOrderedFileIds(searchState(again))).toEqual([
            "b-0",
            "b-1",
        ]);
        expect(selectLoadedFiles(searchState(again))).toBe(2);
    });

    it("restarts the order on a new query rather than growing it", () => {
        const paged = pagedTwice();
        const newQuery = searchSlice.reducer(
            paged,
            resultsReported("q2", "bar", hits(2, "d")),
        );

        expect(selectOrderedFileIds(searchState(newQuery))).toEqual([
            "d-0",
            "d-1",
        ]);
    });

    it("leads with the temporary card, matching the rendered order", () => {
        const withTemporary = searchSlice.reducer(
            pagedTwice(),
            setTemporaryFileId("late"),
        );

        expect(selectOrderedFileIds(searchState(withTemporary))).toEqual([
            "late",
            "b-0",
            "b-1",
            "b-2",
            "c-0",
            "c-1",
        ]);
    });

    it("does not list a temporary id that is also a hit", () => {
        const withTemporary = searchSlice.reducer(
            pagedTwice(),
            setTemporaryFileId("b-1"),
        );
        const ordered = selectOrderedFileIds(searchState(withTemporary));

        expect(ordered).toHaveLength(new Set(ordered).size);
        expect(ordered).toEqual(["b-0", "b-1", "b-2", "c-0", "c-1"]);
    });

    it("keeps its identity while only the file cache changes", () => {
        const paged = pagedTwice();
        const before = selectOrderedFileIds(searchState(paged));

        const withPreview = searchSlice.reducer(paged, previewReported("b-0"));

        expect(selectOrderedFileIds(searchState(withPreview))).toBe(before);
    });
});

describe("paging at the end of the list", () => {
    const atTheBoundary = () => {
        const firstPage = searchSlice.reducer(emptySearchState(), {
            type: updateQuery.fulfilled.type,
            payload: {
                query: queryWithId("q1", "foo"),
                files: hits(3, "b"),
                totalFiles: 9,
            },
        });
        return searchSlice.reducer(firstPage, setHighlightedFileId("b-2"));
    };

    it("reports a page request of its own, not the global loading state", () => {
        const pending = searchSlice.reducer(atTheBoundary(), {
            type: fetchNextPage.pending.type,
        });

        expect(selectIsPaginating(searchState(pending))).toBe(true);
        expect(selectIsPaginating(searchState(atTheBoundary()))).toBe(false);
    });

    it("spends one queued move on the first card of the new page", () => {
        const queued = searchSlice.reducer(
            atTheBoundary(),
            queueResultAdvance(1),
        );
        const landed = searchSlice.reducer(
            queued,
            nextPageReported(hits(3, "c", 3), [2]),
        );

        expect(landed.highlightedFileId).toBe("c-0");
        expect(landed.pagination.queuedAdvance).toBe(0);
    });

    // A press that arrives while the page is in flight is queued, not dropped:
    // a boolean intent would let five presses advance one card.
    it("spends every queued move, not just the first", () => {
        let state = atTheBoundary();
        for (let press = 0; press < 3; press += 1) {
            state = searchSlice.reducer(state, queueResultAdvance(1));
        }
        const landed = searchSlice.reducer(
            state,
            nextPageReported(hits(3, "c", 3), [2]),
        );

        expect(landed.highlightedFileId).toBe("c-2");
    });

    it("clamps a queue longer than the page that arrives", () => {
        const queued = searchSlice.reducer(
            atTheBoundary(),
            queueResultAdvance(10),
        );
        const landed = searchSlice.reducer(
            queued,
            nextPageReported(hits(2, "c", 3), [2]),
        );

        expect(landed.highlightedFileId).toBe("c-1");
    });

    it("moves the scroll request so the pending row can be reached", () => {
        const before = atTheBoundary();
        const queued = searchSlice.reducer(before, queueResultAdvance(1));

        expect(queued.highlightScrollRequest).toBe(
            before.highlightScrollRequest + 1,
        );
    });

    // Nulling an exhausted cursor while the total still claims more leaves the
    // button offering a page that would restart from page one.
    it("stops offering more once a page comes back empty", () => {
        const exhausted = searchSlice.reducer(
            atTheBoundary(),
            nextPageReported([], [2]),
        );

        expect(exhausted.lastFileSortId).toBeNull();
        expect(selectTotalFiles(searchState(exhausted))).toBe(3);
        expect(selectHasMoreResults(searchState(exhausted))).toBe(false);
    });

    it("keeps offering more while the cursor and the total agree", () => {
        expect(selectHasMoreResults(searchState(atTheBoundary()))).toBe(true);
    });

    it("drops a page that was still in flight when a new query landed", () => {
        const newQuery = searchSlice.reducer(
            atTheBoundary(),
            resultsReported("q2", "bar", hits(2, "d"), 5),
        );
        const stalePage = searchSlice.reducer(
            newQuery,
            nextPageReported(hits(3, "c", 3), [2]),
        );

        expect(selectOrderedFileIds(searchState(stalePage))).toEqual([
            "d-0",
            "d-1",
        ]);
    });
});

describe("prefetched pages", () => {
    const withFirstPage = () =>
        searchSlice.reducer(emptySearchState(), {
            type: updateQuery.fulfilled.type,
            payload: {
                query: queryWithId("q1", "foo"),
                files: hits(3, "b"),
                totalFiles: 9,
            },
        });

    const prefetchReported = (
        files: ReturnType<typeof hits>,
        cursor: any[],
    ) => ({
        type: prefetchNextPage.fulfilled.type,
        payload: { files, cursorKey: cursorKey(cursor), fromStaged: false },
    });

    it("stages a page without showing it", () => {
        const staged = searchSlice.reducer(
            withFirstPage(),
            prefetchReported(hits(3, "c", 3), [2]),
        );

        expect(staged.pagination.staged?.files).toHaveLength(3);
        expect(selectLoadedFiles(searchState(staged))).toBe(3);
        expect(selectOrderedFileIds(searchState(staged))).not.toContain("c-0");
    });

    it("drops a page staged for a cursor the list has moved past", () => {
        const staged = searchSlice.reducer(
            withFirstPage(),
            prefetchReported(hits(3, "c", 3), [99]),
        );

        expect(staged.pagination.staged).toBeNull();
    });

    it("clears the staged page once it has been shown", () => {
        const staged = searchSlice.reducer(
            withFirstPage(),
            prefetchReported(hits(3, "c", 3), [2]),
        );
        const shown = searchSlice.reducer(
            staged,
            nextPageReported(hits(3, "c", 3), [2]),
        );

        expect(shown.pagination.staged).toBeNull();
        expect(selectLoadedFiles(searchState(shown))).toBe(6);
    });

    it("discards a staged page when a new query arrives", () => {
        const staged = searchSlice.reducer(
            withFirstPage(),
            prefetchReported(hits(3, "c", 3), [2]),
        );
        const newQuery = searchSlice.reducer(
            staged,
            resultsReported("q2", "bar", hits(2, "d")),
        );

        expect(newQuery.pagination.staged).toBeNull();
    });
});

describe("temporary highlight that re-enters the results", () => {
    const temporaryThenPaged = () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(2, "b"), 3),
        );
        const withTemporary = searchSlice.reducer(
            results,
            setTemporaryFileId("late"),
        );

        // Next page of the same query now returns the highlighted file.
        return searchSlice.reducer(
            withTemporary,
            nextPageReported([{ fileId: "late", sortId: [2] }], [1]),
        );
    };

    const temporaryThenRenewed = () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(2, "b"), 3),
        );
        const withTemporary = searchSlice.reducer(
            results,
            setTemporaryFileId("late"),
        );

        return searchSlice.reducer(withTemporary, {
            type: updateQuery.fulfilled.type,
            payload: {
                query: queryWithId("q2", "foo"),
                files: [...hits(2, "b"), { fileId: "late", sortId: [2] }],
                totalFiles: 3,
            },
        });
    };

    const cachedThenPaged = () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(2, "b"), 3),
        );
        const withPreview = searchSlice.reducer(
            results,
            previewReported("late"),
        );
        const withTemporary = searchSlice.reducer(
            withPreview,
            setTemporaryFileId("late"),
        );

        return searchSlice.reducer(
            withTemporary,
            nextPageReported([{ fileId: "late", sortId: [2] }], [1]),
        );
    };

    it.each([
        ["same query id, next page", temporaryThenPaged],
        ["renewed query id, same query string", temporaryThenRenewed],
        ["entry cached before it was highlighted", cachedThenPaged],
    ])("stops treating it as temporary (%s)", (_name, scenario) => {
        const state = scenario();

        expect(state.files["late"].temporary).toBe(false);
        expect(state.temporaryFileId).toBeNull();
        expect(selectLoadedFiles(searchState(state))).toBe(3);
        expectWithinTotal(state);
    });

    it("lists it once, at its rank, so it is not rendered twice", () => {
        const ordered = selectOrderedFileIds(searchState(temporaryThenPaged()));

        expect(ordered).toHaveLength(new Set(ordered).size);
        expect(ordered).toEqual(["b-0", "b-1", "late"]);
    });

    it("drops a flag the highlight left on an open tab", () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(2, "b"), 3),
        );
        const withTemporary = searchSlice.reducer(
            results,
            setTemporaryFileId("late"),
        );
        const withTab = searchSlice.reducer(
            withTemporary,
            openFileTab({ fileId: "late" }),
        );

        const newQuery = searchSlice.reducer(
            withTab,
            resultsReported("q2", "bar", hits(3, "c")),
        );

        // selectOrderedFileIds reads `temporaryFileId`, so a carried-over flag
        // cannot put a card-less id in the index space. The flag is
        // still cleared: an entry that kept it would claim for the rest of its
        // life to exist only for a highlight that ended with the last query.
        expect(newQuery.files["late"].temporary).toBe(false);
        expect(newQuery.temporaryFileId).toBeNull();
        expect(selectOrderedFileIds(searchState(newQuery))).not.toContain(
            "late",
        );
        expect(selectLoadedFiles(searchState(newQuery))).toBe(3);
    });
});

describe("revealFileThunk", () => {
    beforeEach(() => {
        mockGetFile.mockReset();
        mockGetFile.mockResolvedValue({
            fileId: "test-file",
            preview: { parentId: "parent-file" },
        });
    });

    it("highlights a file not in results and sets temporaryFileId", async () => {
        const store = configureStore({
            reducer: { search: searchSlice.reducer },
        });

        await store.dispatch(revealFileThunk({ fileId: "not-in-results" }));

        const state = store.getState().search;
        expect(state.temporaryFileId).toBe("not-in-results");
        expect(state.highlightedFileId).toBe("not-in-results");
        // Revealing moves the highlight and nothing else: no tab, and the
        // File Detail sidebar is left exactly as the reader had it.
        expect(state.openFileTabs).toEqual([]);
        expect(state.fileDetailSelection).toEqual({ kind: "follow" });
        expect(state.rightSidebarTab).toBeNull();
    });

    it("highlights a file already highlighted without refetching", async () => {
        const store = configureStore({
            reducer: { search: searchSlice.reducer },
        });

        store.dispatch({
            type: "search/setHighlightedFileId",
            payload: "already-highlighted",
        });

        await store.dispatch(
            revealFileThunk({ fileId: "already-highlighted" }),
        );

        const state = store.getState().search;
        expect(state.highlightedFileId).toBe("already-highlighted");
        expect(state.temporaryFileId).toBeNull();
        expect(state.fileDetailSelection).toEqual({ kind: "follow" });
    });
});

describe("which result the user is on", () => {
    const withResults = (count: number, totalFiles = count) =>
        searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(count, "b"), totalFiles),
        );

    const showingRows = (
        state: SearchStateSlice,
        startIndex: number,
        endIndex: number,
    ) =>
        searchSlice.reducer(
            state,
            visibleRangeChanged({ startIndex, endIndex }),
        );

    const rankIn = (state: SearchStateSlice) =>
        selectCurrentResultRank(searchState(state));

    it("reports nothing before the list has said where it is", () => {
        expect(rankIn(withResults(10))).toBeNull();
    });

    it("follows the highlight while its card is on screen", () => {
        const state = searchSlice.reducer(
            showingRows(withResults(50, 200), 20, 25),
            setHighlightedFileId("b-22"),
        );

        expect(rankIn(state)).toBe(23);
    });

    // Reading the top of the viewport instead could never reach the total: the
    // last screenful does not scroll, so the top of it stays a screen short.
    it("reaches the end of the list when the last result is highlighted", () => {
        const state = searchSlice.reducer(
            showingRows(withResults(106), 103, 105),
            setHighlightedFileId("b-105"),
        );

        expect(rankIn(state)).toBe(106);
    });

    it("moves one result at a time near the end", () => {
        const atTheBottom = showingRows(withResults(106), 103, 105);

        expect(
            rankIn(
                searchSlice.reducer(atTheBottom, setHighlightedFileId("b-105")),
            ),
        ).toBe(106);
        expect(
            rankIn(
                searchSlice.reducer(atTheBottom, setHighlightedFileId("b-104")),
            ),
        ).toBe(105);
    });

    // A highlight the user has scrolled away from is no longer where they are.
    it("falls back to the lowest visible result once the highlight is off screen", () => {
        const state = searchSlice.reducer(
            showingRows(withResults(500), 300, 306),
            setHighlightedFileId("b-2"),
        );

        expect(rankIn(state)).toBe(307);
    });

    it("reports the end of the list when scrolled to the bottom", () => {
        expect(rankIn(showingRows(withResults(106), 103, 105))).toBe(106);
    });

    // The rank counts results, but rows lead with the temporary
    // out-of-results card when there is one.
    it("does not count the temporary card as a result", () => {
        const withTemporary = searchSlice.reducer(
            withResults(50, 200),
            setTemporaryFileId("late"),
        );

        expect(rankIn(showingRows(withTemporary, 0, 10))).toBe(10);
    });

    it("ignores a highlight on the temporary card, which has no rank", () => {
        const withTemporary = searchSlice.reducer(
            withResults(50, 200),
            setTemporaryFileId("late"),
        );
        const state = searchSlice.reducer(
            showingRows(withTemporary, 0, 5),
            setHighlightedFileId("late"),
        );

        expect(rankIn(state)).toBe(5);
    });

    it("forgets where it was when a new query replaces the list", () => {
        const scrolled = showingRows(withResults(50, 200), 30, 36);
        const newQuery = searchSlice.reducer(
            scrolled,
            resultsReported("q2", "bar", hits(2, "d")),
        );

        expect(rankIn(newQuery)).toBeNull();
    });
});

describe("a page request that fails", () => {
    const atTheBoundary = () =>
        searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "b"), 9),
        );

    const failedWith = (payload: unknown, condition = false) => ({
        type: fetchNextPage.rejected.type,
        payload,
        meta: { condition },
    });

    // Pages load on their own as the user scrolls, so a failure that left no
    // trace would read as "that is all there is".
    it("records why, so the list can stop and say something", () => {
        const failed = searchSlice.reducer(
            atTheBoundary(),
            failedWith({ kind: "failed", detail: "boom" }),
        );

        expect(selectPaginationError(searchState(failed))).toEqual({
            kind: "failed",
            detail: "boom",
        });
        expect(selectIsPaginating(searchState(failed))).toBe(false);
    });

    // An expired point-in-time cannot be resumed mid-list — the cursor holds
    // sort values that only mean something inside the old snapshot — so it is
    // kept apart from an ordinary failure, which can simply be retried.
    it("keeps an expired snapshot apart from an ordinary failure", () => {
        const expired = searchSlice.reducer(
            atTheBoundary(),
            failedWith({ kind: "expired", detail: "gone" }),
        );

        expect(selectPaginationError(searchState(expired))?.kind).toBe(
            "expired",
        );
    });

    // The condition guard rejects when a request for this page is already in
    // flight. That is not a failure and must not stop the auto-loading.
    it("ignores a rejection from the in-flight guard", () => {
        const guarded = searchSlice.reducer(
            atTheBoundary(),
            failedWith(undefined, true),
        );

        expect(selectPaginationError(searchState(guarded))).toBeNull();
    });

    it("clears the error once a request is under way again", () => {
        const failed = searchSlice.reducer(
            atTheBoundary(),
            failedWith({ kind: "failed", detail: "boom" }),
        );
        const retrying = searchSlice.reducer(failed, {
            type: fetchNextPage.pending.type,
        });

        expect(selectPaginationError(searchState(retrying))).toBeNull();
    });

    it("clears the error on a new query", () => {
        const failed = searchSlice.reducer(
            atTheBoundary(),
            failedWith({ kind: "expired", detail: "gone" }),
        );
        const newQuery = searchSlice.reducer(
            failed,
            resultsReported("q2", "bar", hits(2, "d")),
        );

        expect(selectPaginationError(searchState(newQuery))).toBeNull();
    });
});

describe("cards entering and leaving the viewport", () => {
    const withResults = () =>
        searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(3, "b")),
        );

    const inView = (fileId: string, visible: boolean) =>
        fileInViewChanged({ fileId, inView: visible });

    it("records a card that scrolls in", () => {
        const state = searchSlice.reducer(withResults(), inView("b-1", true));

        expect(selectFilesInView(searchState(state))).toEqual(["b-1"]);
    });

    it("records a card once however often it is reported", () => {
        let state = searchSlice.reducer(withResults(), inView("b-1", true));
        state = searchSlice.reducer(state, inView("b-1", true));

        expect(selectFilesInView(searchState(state))).toEqual(["b-1"]);
    });

    // The list is windowed, so scrolling unmounts cards that are still in
    // view. The card dispatches this from its effect cleanup; without it the
    // id would sit in filesInView for the rest of the query and be reported to
    // the chat agent as something the user is looking at.
    it("drops a card unmounted while still in view", () => {
        const scrolledIn = searchSlice.reducer(
            withResults(),
            inView("b-1", true),
        );
        const unmounted = searchSlice.reducer(scrolledIn, inView("b-1", false));

        expect(selectFilesInView(searchState(unmounted))).toEqual([]);
    });

    // The add is guarded against an unknown id; the removal must not be, or an
    // entry evicted from the cache while on screen can never leave the list.
    it("drops a card whose cache entry is already gone", () => {
        const scrolledIn = searchSlice.reducer(
            withResults(),
            inView("b-1", true),
        );
        const newQuery = searchSlice.reducer(
            scrolledIn,
            resultsReported("q2", "bar", hits(2, "d")),
        );
        const stillLeaving = searchSlice.reducer(
            { ...newQuery, filesInView: ["b-1"] },
            inView("b-1", false),
        );

        expect(selectFilesInView(searchState(stillLeaving))).toEqual([]);
    });

    it("ignores a card that is not in the cache", () => {
        const state = searchSlice.reducer(withResults(), inView("ghost", true));

        expect(selectFilesInView(searchState(state))).toEqual([]);
    });

    // filesInView is appended to in scroll order, so scrolling up builds it
    // backwards. Anything reporting the visible cards wants them as rendered.
    it("reports the visible cards in rank order", () => {
        let state = withResults();
        for (const id of ["b-2", "b-0", "b-1"]) {
            state = searchSlice.reducer(state, inView(id, true));
        }

        expect(selectFilesInView(searchState(state))).toEqual([
            "b-2",
            "b-0",
            "b-1",
        ]);
        expect(selectFilesInViewOrdered(searchState(state))).toEqual([
            "b-0",
            "b-1",
            "b-2",
        ]);
    });
});

describe("re-render guards", () => {
    it("returns the same state when the highlight is re-asserted", () => {
        const highlighted = searchSlice.reducer(
            emptySearchState(),
            setHighlightedFileId("a-0"),
        );

        const again = searchSlice.reducer(
            highlighted,
            setHighlightedFileId("a-0"),
        );

        // Identity, not equality: a new state object notifies every subscriber
        // and re-arms the auto-actions timer for a highlight that did not move.
        expect(again).toBe(highlighted);
    });

    // Every mounted card subscribes to this selector, so an object rebuilt
    // per action re-renders all of them. Taking the whole search slice as the
    // input is exactly what does that, since its identity changes constantly.
    it("keeps card visibility referentially stable across unrelated actions", () => {
        const state = emptySearchState();
        const before = selectCardElementVisibility(searchState(state));

        const unrelated = searchSlice.reducer(
            state,
            setHighlightedFileId("a-0"),
        );

        expect(selectCardElementVisibility(searchState(unrelated))).toBe(
            before,
        );
    });

    it("gives a new card visibility object when a flag actually changes", () => {
        const state = emptySearchState();
        const before = selectCardElementVisibility(searchState(state));

        const toggled = searchSlice.reducer(
            state,
            setShowTags(!before.showTags),
        );

        expect(selectCardElementVisibility(searchState(toggled))).not.toBe(
            before,
        );
        expect(selectCardElementVisibility(searchState(toggled)).showTags).toBe(
            !before.showTags,
        );
    });
});

describe("sidebar widths", () => {
    it("clamps a width below the minimum", () => {
        const narrowed = searchSlice.reducer(
            emptySearchState(),
            setLeftSidebarWidth(10),
        );

        expect(selectLeftSidebarWidth(searchState(narrowed))).toBe(14 * 16);
    });

    it("clamps a width that would squeeze the centre column", () => {
        const widened = searchSlice.reducer(
            emptySearchState(),
            setRightSidebarWidth(window.innerWidth + 1000),
        );

        expect(selectRightSidebarWidth(searchState(widened))).toBe(
            Math.max(14 * 16, window.innerWidth - 20 * 16),
        );
    });
});

describe("fields the reader picked out", () => {
    const withSelection = (fields: string[]) =>
        searchSlice.reducer(emptySearchState(), setPreviewFields(fields));

    it("turns the emphasis on and off again", () => {
        let state = withSelection(["content", "path"]);

        state = searchSlice.reducer(state, toggleBoldPreviewField("path"));
        expect(selectBoldPreviewFields(searchState(state))).toEqual(["path"]);

        state = searchSlice.reducer(state, toggleBoldPreviewField("path"));
        expect(selectBoldPreviewFields(searchState(state))).toEqual([]);
    });

    it("drops the emphasis when the field leaves the selection", () => {
        // Otherwise deselecting a field and selecting it again brings back a
        // bold the reader has no way of seeing they still have.
        let state = withSelection(["content", "path"]);
        state = searchSlice.reducer(state, toggleBoldPreviewField("path"));

        state = searchSlice.reducer(state, setPreviewFields(["content"]));

        expect(selectBoldPreviewFields(searchState(state))).toEqual([]);
    });
});

describe("the card's field columns", () => {
    const withSelection = (fields: string[]) =>
        searchSlice.reducer(emptySearchState(), setPreviewFields(fields));

    const twoColumns = (fields: string[]) =>
        searchSlice.reducer(withSelection(fields), addFieldColumn());

    it("moves a field across and back", () => {
        let state = twoColumns(["content", "path"]);

        state = searchSlice.reducer(
            state,
            setPreviewFieldColumn({ fieldId: "path", column: 1 }),
        );
        expect(selectFieldColumnOf(searchState(state))).toEqual({ path: 1 });

        state = searchSlice.reducer(
            state,
            setPreviewFieldColumn({ fieldId: "path", column: 0 }),
        );
        expect(selectFieldColumnOf(searchState(state))).toEqual({ path: 0 });
    });

    it("clamps a column the card does not have", () => {
        // The drop zones only offer the columns that exist, but the action is
        // also where a drag lands and a drag can outlive the zone it started
        // from.
        const state = searchSlice.reducer(
            withSelection(["content"]),
            setPreviewFieldColumn({ fieldId: "content", column: 3 }),
        );

        expect(selectFieldColumnOf(searchState(state))).toEqual({ content: 0 });
    });

    it("ignores a field that is not selected", () => {
        const state = searchSlice.reducer(
            withSelection(["content"]),
            setPreviewFieldColumn({ fieldId: "path", column: 0 }),
        );

        expect(selectFieldColumnOf(searchState(state))).toEqual({});
    });

    it("forgets the column of a deselected field", () => {
        let state = twoColumns(["content", "path"]);
        state = searchSlice.reducer(
            state,
            setPreviewFieldColumn({ fieldId: "path", column: 1 }),
        );

        state = searchSlice.reducer(state, setPreviewFields(["content"]));

        expect(selectFieldColumnOf(searchState(state))).toEqual({});
    });

    it("brings the fields of a removed column back rather than dropping them", () => {
        // Removing a column is about the layout. A reader who meant to drop
        // the fields would have removed the fields.
        let state = twoColumns(["content", "path"]);
        state = searchSlice.reducer(
            state,
            setPreviewFieldColumn({ fieldId: "path", column: 1 }),
        );

        state = searchSlice.reducer(state, removeFieldColumn());

        expect(selectFieldColumnCount(searchState(state))).toBe(1);
        expect(selectFieldColumnOf(searchState(state))).toEqual({ path: 0 });
    });

    it("never goes below one column or above the cap", () => {
        let state = searchSlice.reducer(
            emptySearchState(),
            removeFieldColumn(),
        );
        expect(selectFieldColumnCount(searchState(state))).toBe(1);

        for (let i = 0; i < MAX_FIELD_COLUMNS + 3; i += 1) {
            state = searchSlice.reducer(state, addFieldColumn());
        }
        expect(selectFieldColumnCount(searchState(state))).toBe(
            MAX_FIELD_COLUMNS,
        );
    });
});

describe("which File Detail tab is in front", () => {
    const withTabs = (...fileIds: string[]) =>
        fileIds.reduce(
            (state, fileId) =>
                searchSlice.reducer(state, openFileTab({ fileId })),
            emptySearchState(),
        );

    it("comes back to the following tab when the highlight moves", () => {
        // Moving the highlight is asking about a different file, so the
        // parked document stops being the one in front - but stays open.
        const onATab = withTabs("a");

        const moved = searchSlice.reducer(
            onATab,
            setHighlightedFileId("elsewhere"),
        );

        expect(moved.fileDetailSelection).toEqual({ kind: "follow" });
        expect(moved.openFileTabs).toHaveLength(1);
    });

    it("stays put when the highlight is only re-asserted", () => {
        const onATab = searchSlice.reducer(
            withTabs("a"),
            setHighlightedFileId("a"),
        );
        const reselected = searchSlice.reducer(onATab, focusFileTab("a"));

        const again = searchSlice.reducer(
            reselected,
            setHighlightedFileId("a"),
        );

        expect(again.fileDetailSelection).toEqual({
            kind: "file",
            fileId: "a",
        });
    });

    it("falls back to the following tab when the tab in front is closed", () => {
        // Never to a neighbour: the reader asked to be rid of this document,
        // not to be handed the one beside it.
        const onB = withTabs("a", "b");

        const closed = searchSlice.reducer(onB, closeFileTab("b"));

        expect(closed.fileDetailSelection).toEqual({ kind: "follow" });
        expect(closed.openFileTabs.map((t) => t.fileId)).toEqual(["a"]);
    });

    it("leaves the reader alone when another tab is closed", () => {
        const onB = withTabs("a", "b");

        const closed = searchSlice.reducer(onB, closeFileTab("a"));

        expect(closed.fileDetailSelection).toEqual({
            kind: "file",
            fileId: "b",
        });
    });
});
