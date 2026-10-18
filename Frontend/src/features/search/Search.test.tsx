import { configureStore } from "@reduxjs/toolkit";
import { act, fireEvent, render, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { MemoryRouter, useLocation, useNavigate } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SEARCH_STATE_LOCAL_STORAGE_KEY } from "@app/slices/searchSlice";

// Mounting Search pulls in the whole workspace; the first dynamic import in a
// run pays for transforming it.
vi.setConfig({ testTimeout: 30_000 });

const { apiMock, mockGetFilesCount, mockGetLongRunningQuery, mockSearchFiles } =
    vi.hoisted(() => {
        const getFilesCount = vi.fn();
        const getLongRunningQuery = vi.fn();
        const searchFiles = vi.fn();
        return {
            apiMock: {
                getFilePreview: vi.fn(),
                getFilesCount,
                getLongRunningQuery,
                loadSummarizationSystemPrompt: vi.fn(async () => ""),
                loadTags: vi.fn(async () => []),
                loadVisionSystemPrompt: vi.fn(async () => ""),
                ResponseError: class ResponseError extends Error {},
                searchFiles,
            },
            mockGetFilesCount: getFilesCount,
            mockGetLongRunningQuery: getLongRunningQuery,
            mockSearchFiles: searchFiles,
        };
    });

vi.mock("@app/api", () => apiMock);
vi.mock("@app/api/index", () => apiMock);

vi.mock("@middleware/SocketMiddleware", () => ({
    default: () => () => (next: unknown) => next,
    webSocketSendMessage: vi.fn(() => ({ type: "socket/send" })),
    websocketConnect: { type: "socket/connect" },
    websocketDisconnect: { type: "socket/disconnect" },
}));

vi.mock("@features/search/components/ActivityBar/ActivityBar", () => ({
    ActivityBar: () => null,
}));
vi.mock("@features/search/components/CenterTabs/CenterTabs", () => ({
    CenterTabs: () => null,
}));
vi.mock("@features/search/components/LeftSidebar/LeftSidebar", () => ({
    LeftSidebar: () => null,
}));
vi.mock("@features/search/components/RightSidebar/RightSidebar", () => ({
    RightSidebar: () => null,
}));
vi.mock("@features/search/hooks/useKeyboardNavigation", () => ({
    useKeyboardNavigation: () => undefined,
}));

const SORTED_SEARCH =
    "?query=eml&sortField=tika_meta.dcterms_created&sortDirection=desc";
const SORTED_URL = `/search${SORTED_SEARCH}`;

const SORTED_QUERY = {
    id: "pit-from-last-session",
    query: "eml",
    sortField: "tika_meta.dcterms_created",
    sortDirection: "desc",
    sortId: "cursor-from-last-session",
};

/** Seed the query the slice restores on load. The results are never persisted,
 *  which is the whole reason a restored query has to be searched again. */
const persistQuery = (query: Record<string, unknown>) =>
    window.localStorage.setItem(
        SEARCH_STATE_LOCAL_STORAGE_KEY,
        JSON.stringify({ query }),
    );

const UrlHarness = () => {
    const location = useLocation();
    const navigate = useNavigate();
    return (
        <>
            <span data-testid="location-search">{location.search}</span>
            <button onClick={() => navigate("/search?query=other")}>
                Go to other query
            </button>
        </>
    );
};

const renderSearch = async (url: string) => {
    const { Search } = await import("./Search");
    const { default: searchReducer } = await import("@app/slices/searchSlice");
    const { default: commonReducer } = await import("@app/slices/commonSlice");
    const store = configureStore({
        reducer: { common: commonReducer, search: searchReducer },
        middleware: (getDefaultMiddleware) =>
            getDefaultMiddleware({ serializableCheck: false }),
    });
    const view = render(
        <Provider store={store}>
            <MemoryRouter initialEntries={[url]}>
                <Search />
                <UrlHarness />
            </MemoryRouter>
        </Provider>,
    );
    const locationSearch = () =>
        view.getByTestId("location-search").textContent;
    return { locationSearch, store, view };
};

describe("Search URL synchronisation", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.resetModules();
        window.localStorage.clear();
        mockGetLongRunningQuery.mockResolvedValue({ queryId: "pit-new" });
        mockSearchFiles.mockResolvedValue({ files: [] });
        mockGetFilesCount.mockResolvedValue({ totalFiles: 0 });
    });

    it("searches what the URL asks for when nothing is cached", async () => {
        await renderSearch(SORTED_URL);

        await waitFor(() => expect(mockSearchFiles).toHaveBeenCalledTimes(1));
        expect(mockSearchFiles).toHaveBeenCalledWith(
            expect.objectContaining({
                query: "eml",
                sortField: "tika_meta.dcterms_created",
                sortDirection: "desc",
            }),
        );
    });

    it("searches what the URL asks for over a different cached query", async () => {
        persistQuery({
            id: "pit-from-last-session",
            query: "something-else",
            sortField: null,
            sortDirection: null,
            sortId: null,
        });

        await renderSearch(SORTED_URL);

        await waitFor(() => expect(mockSearchFiles).toHaveBeenCalledTimes(1));
        expect(mockSearchFiles).toHaveBeenCalledWith(
            expect.objectContaining({ query: "eml" }),
        );
    });

    it("searches what the URL asks for even when it is the cached query", async () => {
        // A link pasted back into the browser that produced it, or a plain
        // reload: the restored query matches the URL while the results are
        // gone, and matching the two used to count as "nothing to do".
        persistQuery(SORTED_QUERY);

        await renderSearch(SORTED_URL);

        await waitFor(() => expect(mockSearchFiles).toHaveBeenCalledTimes(1));
        expect(mockSearchFiles).toHaveBeenCalledWith(
            expect.objectContaining({
                query: "eml",
                sortField: "tika_meta.dcterms_created",
                sortDirection: "desc",
                // The cursor into last session's snapshot cannot be resumed.
                sortId: null,
            }),
        );
    });

    it("reads a URL without sort params as an unsorted search", async () => {
        persistQuery({
            id: "pit-from-last-session",
            query: "something-else",
            sortField: "short_name",
            sortDirection: "asc",
            sortId: null,
        });

        await renderSearch("/search?query=eml");

        await waitFor(() => expect(mockSearchFiles).toHaveBeenCalledTimes(1));
        expect(mockSearchFiles).toHaveBeenCalledWith(
            expect.objectContaining({
                query: "eml",
                sortField: null,
                sortDirection: null,
            }),
        );
    });

    it("re-runs the cached query when the URL names none", async () => {
        persistQuery(SORTED_QUERY);

        const { locationSearch } = await renderSearch("/search");

        await waitFor(() => expect(mockSearchFiles).toHaveBeenCalledTimes(1));
        expect(mockSearchFiles).toHaveBeenCalledWith(
            expect.objectContaining({
                query: "eml",
                sortField: "tika_meta.dcterms_created",
                sortDirection: "desc",
            }),
        );
        await waitFor(() => expect(locationSearch()).toBe(SORTED_SEARCH));
    });

    it("does not search the URL it wrote itself a second time", async () => {
        const { locationSearch, store } =
            await renderSearch("/search?query=eml");
        await waitFor(() => expect(mockSearchFiles).toHaveBeenCalledTimes(1));
        const { updateQuery } = await import("@app/slices/searchSlice");

        await act(async () => {
            await store.dispatch(updateQuery({ query: "pdf" }));
        });

        expect(mockSearchFiles).toHaveBeenCalledTimes(2);
        await waitFor(() => expect(locationSearch()).toBe("?query=pdf"));
        await act(
            () => new Promise((resolve) => window.setTimeout(resolve, 50)),
        );
        expect(mockSearchFiles).toHaveBeenCalledTimes(2);
    });

    it("searches again when a navigation changes the query", async () => {
        const { view } = await renderSearch("/search?query=eml");
        await waitFor(() => expect(mockSearchFiles).toHaveBeenCalledTimes(1));

        fireEvent.click(
            view.getByRole("button", { name: "Go to other query" }),
        );

        await waitFor(() => expect(mockSearchFiles).toHaveBeenCalledTimes(2));
        expect(mockSearchFiles).toHaveBeenLastCalledWith(
            expect.objectContaining({ query: "other" }),
        );
    });
});
