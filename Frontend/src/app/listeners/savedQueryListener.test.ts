import { configureStore } from "@reduxjs/toolkit";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import searchReducer, {
    addCustomQuery,
    deleteCustomQuery,
    initCustomQuery,
} from "@app/slices/searchSlice";
import { SearchQuery } from "@features/common/utils/model";
import {
    websocketConnect,
    websocketDisconnect,
} from "@middleware/SocketMiddleware";

import {
    SAVED_QUERY_COUNT_POLL_INTERVAL_MS,
    createSavedQueryListenerMiddleware,
} from "./savedQueryListener";

const mockGetFilesCount = vi.hoisted(() => vi.fn());

// Stub only the one network call the loop makes; everything else in the api
// barrel stays real so the slice behaves normally.
vi.mock("@app/api/index", async (importOriginal) => ({
    ...(await importOriginal<typeof import("@app/api/index")>()),
    getFilesCount: mockGetFilesCount,
}));

vi.mock("i18next", () => ({ t: (key: string) => key }));
vi.mock("react-toastify", () => ({ toast: { error: vi.fn() } }));

const searchQuery = (query: string): SearchQuery => ({
    id: null,
    query,
    keepAlive: null,
    sortField: null,
    sortDirection: null,
    sortId: null,
    pageSize: null,
});

// Every store started here must be stopped again: a running loop holds a
// visibilitychange handler on the shared jsdom document, which would otherwise
// fire into a previous test's store.
const startedStores: { dispatch: (action: unknown) => unknown }[] = [];

const makeStore = (queries: string[]) => {
    const store = configureStore({
        reducer: { search: searchReducer },
        middleware: (getDefaultMiddleware) =>
            getDefaultMiddleware().prepend(
                createSavedQueryListenerMiddleware().middleware,
            ),
    });
    startedStores.push(store as { dispatch: (action: unknown) => unknown });
    queries.forEach((query, index) =>
        store.dispatch(
            addCustomQuery(
                initCustomQuery(
                    searchQuery(query),
                    0,
                    `Query ${index}`,
                    "Tune",
                ),
            ),
        ),
    );
    return store;
};

// advanceTimersByTimeAsync drains timers, but the poll round awaits one promise
// per saved query after the timer fires, so give the microtask queue room.
const flushMicrotasks = async () => {
    for (let i = 0; i < 20; i += 1) await Promise.resolve();
};

const tick = async (count = 1) => {
    for (let i = 0; i < count; i += 1) {
        await vi.advanceTimersByTimeAsync(SAVED_QUERY_COUNT_POLL_INTERVAL_MS);
        await flushMicrotasks();
    }
};

const searchStringsRequested = () =>
    mockGetFilesCount.mock.calls.map((call) => call[0].query);

let hidden = false;

describe("saved query polling listener", () => {
    beforeEach(() => {
        vi.useFakeTimers();
        hidden = false;
        Object.defineProperty(document, "hidden", {
            configurable: true,
            get: () => hidden,
        });
        mockGetFilesCount.mockReset();
        mockGetFilesCount.mockResolvedValue({ totalFiles: 1 });
    });

    afterEach(async () => {
        startedStores.forEach((store) => store.dispatch(websocketDisconnect));
        startedStores.length = 0;
        await flushMicrotasks();
        vi.useRealTimers();
        // Leaving the override in place would make every later suite in the
        // process think the document is backgrounded.
        Reflect.deleteProperty(document, "hidden");
    });

    it("does not poll before the websocket session starts", async () => {
        makeStore(["a", "b"]);

        await tick(2);

        expect(mockGetFilesCount).not.toHaveBeenCalled();
    });

    it("polls every saved query once per interval", async () => {
        const store = makeStore(["a", "b"]);
        store.dispatch(websocketConnect);

        await tick();

        expect(searchStringsRequested()).toEqual(["a", "b"]);
    });

    it("keeps a steady cadence across intervals for all queries", async () => {
        const store = makeStore(["a", "b", "c"]);
        store.dispatch(websocketConnect);

        await tick(3);

        // Three queries over three intervals. The per-item intervals this
        // replaced were recreated on every response, which reset their clocks.
        expect(mockGetFilesCount).toHaveBeenCalledTimes(9);
    });

    it("does not lose its cadence when the backend is slow", async () => {
        const store = makeStore(["a"]);
        let resolveCount: (value: { totalFiles: number }) => void = () => {};
        mockGetFilesCount.mockImplementationOnce(
            () =>
                new Promise((resolve) => {
                    resolveCount = resolve;
                }),
        );
        store.dispatch(websocketConnect);

        await tick();
        expect(mockGetFilesCount).toHaveBeenCalledTimes(1);
        resolveCount({ totalFiles: 4 });
        await flushMicrotasks();

        await tick();
        expect(mockGetFilesCount).toHaveBeenCalledTimes(2);
    });

    it("picks up queries added and removed mid-session", async () => {
        const store = makeStore(["a"]);
        store.dispatch(websocketConnect);

        await tick();
        expect(searchStringsRequested()).toEqual(["a"]);

        store.dispatch(
            addCustomQuery(initCustomQuery(searchQuery("b"), 0, "B", "Tune")),
        );
        mockGetFilesCount.mockClear();
        await tick();
        expect(searchStringsRequested()).toEqual(["a", "b"]);

        const [first] = store.getState().search.customQueries;
        store.dispatch(deleteCustomQuery(first));
        mockGetFilesCount.mockClear();
        await tick();
        expect(searchStringsRequested()).toEqual(["b"]);
    });

    it("pauses while the tab is hidden and catches up when it returns", async () => {
        const store = makeStore(["a"]);
        store.dispatch(websocketConnect);

        hidden = true;
        await tick(2);
        expect(mockGetFilesCount).not.toHaveBeenCalled();

        hidden = false;
        document.dispatchEvent(new Event("visibilitychange"));
        await flushMicrotasks();

        expect(searchStringsRequested()).toEqual(["a"]);
    });

    it("does not stack rounds when a round outlives the interval", async () => {
        const store = makeStore(["a"]);
        mockGetFilesCount.mockImplementation(() => new Promise(() => {}));
        store.dispatch(websocketConnect);

        await tick(3);

        expect(mockGetFilesCount).toHaveBeenCalledTimes(1);
    });

    it("stops polling on disconnect", async () => {
        const store = makeStore(["a"]);
        store.dispatch(websocketConnect);
        await tick();
        expect(mockGetFilesCount).toHaveBeenCalledTimes(1);

        store.dispatch(websocketDisconnect);
        await tick(2);

        expect(mockGetFilesCount).toHaveBeenCalledTimes(1);
    });

    it("runs a single loop after a reconnect", async () => {
        const store = makeStore(["a"]);
        store.dispatch(websocketConnect);
        store.dispatch(websocketConnect);

        await tick();

        expect(mockGetFilesCount).toHaveBeenCalledTimes(1);
    });

    it("tolerates a disconnect with no loop running", async () => {
        const store = makeStore(["a"]);

        expect(() => store.dispatch(websocketDisconnect)).not.toThrow();

        // StrictMode double-invokes the effect that dispatches these, and the
        // connect is dispatched from an async function while the disconnect
        // fires synchronously from cleanup, so this ordering really happens.
        store.dispatch(websocketConnect);
        await tick();

        expect(mockGetFilesCount).toHaveBeenCalledTimes(1);
    });
});
