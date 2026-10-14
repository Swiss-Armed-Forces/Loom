import { beforeEach, describe, expect, it, vi } from "vitest";

import { SearchQuery } from "@features/common/utils/model";

import { RootState } from "../store";

import {
    CustomQuery,
    addCustomQuery,
    fetchFilesCountForCustomQuery,
    fetchPreview,
    initCustomQuery,
    loadPersistedSearchState,
    markCustomQueryAsRead,
    normalizeCustomQueries,
    openFileTab,
    searchSlice,
    selectLoadedFiles,
    selectOrderedFileIds,
    selectTotalFiles,
    setTemporaryFileId,
    updateQuery,
} from "./searchSlice";

const mockToastError = vi.hoisted(() => vi.fn());

vi.mock("i18next", () => ({
    t: (key: string) => key,
}));

vi.mock("react-toastify", () => ({
    toast: { error: mockToastError },
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

        expect(updated.fileCount).toBe(12);
        expect(updated.hasNewFiles).toBe(true);
        expect(updated.lastSeenCount).toBe(10);
    });

    it("does not move the baseline when the count falls", () => {
        const customQuery = savedQuery();

        const [updated] = searchSlice.reducer(
            stateWith(customQuery),
            countReported(customQuery.id, 4),
        ).customQueries;

        expect(updated.fileCount).toBe(4);
        expect(updated.lastSeenCount).toBe(10);
        expect(updated.hasNewFiles).toBe(false);
    });

    it("still flags new files after a dip back past the baseline", () => {
        const customQuery = savedQuery();
        const state = stateWith(customQuery);

        const afterDip = searchSlice.reducer(
            state,
            countReported(customQuery.id, 4),
        );
        const [recovered] = searchSlice.reducer(
            afterDip,
            countReported(customQuery.id, 11),
        ).customQueries;

        expect(recovered.hasNewFiles).toBe(true);
    });

    it("clears the flag and rebaselines from state, not from the payload", () => {
        const customQuery = savedQuery({ hasNewFiles: true });
        const polled = searchSlice.reducer(
            stateWith(customQuery),
            countReported(customQuery.id, 25),
        );

        // Call sites hold a render-time snapshot; this one still says 10.
        const [updated] = searchSlice.reducer(
            polled,
            markCustomQueryAsRead(customQuery),
        ).customQueries;

        expect(updated.hasNewFiles).toBe(false);
        expect(updated.lastSeenCount).toBe(25);
    });

    it("ignores a count for a query that no longer exists", () => {
        const state = stateWith(savedQuery());

        expect(
            searchSlice.reducer(state, countReported("gone", 99)),
        ).toStrictEqual(state);
    });
});

describe("persisted saved query migration", () => {
    beforeEach(() => window.localStorage.clear());

    it("seeds a missing baseline from the stored count", () => {
        const [migrated] = normalizeCustomQueries([
            { ...savedQuery(), lastSeenCount: undefined },
        ]);

        expect(migrated.lastSeenCount).toBe(10);
        expect(migrated.hasNewFiles).toBe(false);
    });

    it("defaults both counts when the stored count is missing", () => {
        const [migrated] = normalizeCustomQueries([
            {
                id: "q",
                query: SAVED_QUERY,
                name: "Q",
                icon: "Stars",
                hasNewFiles: true,
            },
        ]);

        expect(migrated.fileCount).toBe(0);
        expect(migrated.lastSeenCount).toBe(0);
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

const resultsReported = (
    id: string,
    query: string,
    files: ReturnType<typeof hits>,
) => ({
    type: updateQuery.fulfilled.type,
    payload: { query: queryWithId(id, query), files, totalFiles: files.length },
});

const previewReported = (fileId: string) => ({
    type: fetchPreview.fulfilled.type,
    payload: { query: SAVED_QUERY, preview: { fileId } },
});

const previewFailed = (fileId: string) => ({
    type: fetchPreview.rejected.type,
    payload: { fileId },
});

// Oracle for the counter, cross-checked against the other selector instead of
// re-applying selectLoadedFiles' own predicate: selectOrderedFileIds is the
// result segment followed by the temporary tail, so dropping the tail leaves
// the result cards DetailedView renders.
const resultCardCount = (search: SearchStateSlice) =>
    selectOrderedFileIds(searchState(search)).length -
    Object.values(search.files).filter((f) => f.temporary).length;

// #338 read "13 of 12". The bound holds as long as every counted card is still
// a hit of the reported total, which is the case in every scenario it is
// asserted in below; a stale card can outlive its hit, so the stale test
// deliberately makes no such claim.
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

        // "a-0" is kept so its panel survives, but it is not a hit of "bar".
        const secondQuery = searchSlice.reducer(
            withTab,
            resultsReported("q2", "bar", hits(12, "b")),
        );

        expect(selectLoadedFiles(searchState(secondQuery))).toBe(12);
        expect(selectTotalFiles(searchState(secondQuery))).toBe(12);
        expectWithinTotal(secondQuery);
    });

    it("ignores a preview fetched for a file outside the results", () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(12, "b")),
        );

        // An open tab restored from local storage: the panel fetches a preview
        // for a file the current query never returned.
        const withPreview = searchSlice.reducer(
            results,
            previewReported("outside"),
        );

        expect(selectLoadedFiles(searchState(withPreview))).toBe(12);
        expect(selectTotalFiles(searchState(withPreview))).toBe(12);
        expectWithinTotal(withPreview);
    });

    // Regression guard only: the previous filter excluded `temporary` entries
    // too, so this scenario counted 12 before the fix as well.
    it("ignores the temporary out-of-results highlight", () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(12, "b")),
        );

        const withTemporary = searchSlice.reducer(
            results,
            setTemporaryFileId("outside"),
        );

        expect(selectLoadedFiles(searchState(withTemporary))).toBe(12);
        expectWithinTotal(withTemporary);
    });

    it("reports nothing loaded once the query is cleared", () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(12, "b")),
        );

        // An emptied or aborted query nulls every cached `meta` and zeroes the
        // total; counting cache entries instead reported "12 of 0".
        const cleared = searchSlice.reducer(results, {
            type: updateQuery.fulfilled.type,
            payload: undefined,
        });

        expect(selectLoadedFiles(searchState(cleared))).toBe(0);
        expect(selectTotalFiles(searchState(cleared))).toBe(0);
    });

    it("counts a stale card, which stays on screen", () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(12, "b")),
        );

        const withStale = searchSlice.reducer(results, previewFailed("b-0"));

        expect(selectLoadedFiles(searchState(withStale))).toBe(12);
        expect(selectLoadedFiles(searchState(withStale))).toBe(
            resultCardCount(withStale),
        );
    });

    // Regression guard only: every entry is clean here, so the previous filter
    // also counted 20. It guards against an over-correction that would count
    // just the last page.
    it("counts every page once pagination has loaded them", () => {
        const firstPage = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(12, "b")),
        );

        const secondPage = searchSlice.reducer(firstPage, {
            type: updateQuery.fulfilled.type,
            payload: {
                query: queryWithId("q1", "foo"),
                files: hits(8, "c", 12),
                totalFiles: 20,
            },
        });

        expect(selectLoadedFiles(searchState(secondPage))).toBe(20);
        expect(selectTotalFiles(searchState(secondPage))).toBe(20);
        expect(secondPage.lastFileSortId).toEqual([19]);
        expectWithinTotal(secondPage);
    });
});

describe("temporary highlight that re-enters the results", () => {
    const temporaryThenPaged = () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(2, "b")),
        );
        const withTemporary = searchSlice.reducer(
            results,
            setTemporaryFileId("late"),
        );

        // Next page of the same query now returns the highlighted file.
        return searchSlice.reducer(withTemporary, {
            type: updateQuery.fulfilled.type,
            payload: {
                query: queryWithId("q1", "foo"),
                files: [{ fileId: "late", sortId: [2] }],
                totalFiles: 3,
            },
        });
    };

    // A keep-alive renewal: a new query id with the same query string preserves
    // the highlighted entry through the new-query branch, and the renewed page
    // then returns it as a hit.
    const temporaryThenRenewed = () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(2, "b")),
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

    // The entry already exists when the file is highlighted — a preview was
    // fetched for it, or it has an open tab — so setTemporaryFileId only points
    // `temporaryFileId` at it and never sets the per-entry flag.
    const cachedThenPaged = () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(2, "b")),
        );
        const withPreview = searchSlice.reducer(
            results,
            previewReported("late"),
        );
        const withTemporary = searchSlice.reducer(
            withPreview,
            setTemporaryFileId("late"),
        );

        return searchSlice.reducer(withTemporary, {
            type: updateQuery.fulfilled.type,
            payload: {
                query: queryWithId("q1", "foo"),
                files: [{ fileId: "late", sortId: [2] }],
                totalFiles: 3,
            },
        });
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

    it("lists it once, so it is not rendered twice", () => {
        const ordered = selectOrderedFileIds(searchState(temporaryThenPaged()));

        // Not an ordering assertion: selectOrderedFileIds follows `Object.keys`
        // insertion order and setting `meta` on an existing entry does not
        // re-insert it, so a cached file keeps the position it was created at
        // rather than its sort position. What matters is that it is listed once.
        expect(ordered).toHaveLength(new Set(ordered).size);
        expect(ordered.filter((id) => id === "late")).toHaveLength(1);
        expect(ordered).toEqual(expect.arrayContaining(["b-0", "b-1"]));
    });

    it("drops a flag the highlight left on an open tab", () => {
        const results = searchSlice.reducer(
            emptySearchState(),
            resultsReported("q1", "foo", hits(2, "b")),
        );
        const withTemporary = searchSlice.reducer(
            results,
            setTemporaryFileId("late"),
        );
        // Opening the highlighted file in a tab makes its entry survive the
        // next query, but the highlight itself does not survive.
        const withTab = searchSlice.reducer(
            withTemporary,
            openFileTab({ fileId: "late" }),
        );

        const newQuery = searchSlice.reducer(
            withTab,
            resultsReported("q2", "bar", hits(3, "c")),
        );

        // A carried-over flag has nothing left to clear it, so it would sit in
        // the temporary tail of selectOrderedFileIds with no card to land on.
        expect(newQuery.files["late"].temporary).toBe(false);
        expect(newQuery.temporaryFileId).toBeNull();
        expect(selectOrderedFileIds(searchState(newQuery))).not.toContain(
            "late",
        );
        expect(selectLoadedFiles(searchState(newQuery))).toBe(3);
    });
});
