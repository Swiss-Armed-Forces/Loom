import { beforeEach, describe, expect, it, vi } from "vitest";

import { SearchQuery } from "@features/common/utils/model";

import {
    CustomQuery,
    addCustomQuery,
    fetchFilesCountForCustomQuery,
    initCustomQuery,
    loadPersistedSearchState,
    markCustomQueryAsRead,
    normalizeCustomQueries,
    searchSlice,
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
