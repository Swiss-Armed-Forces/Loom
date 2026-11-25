import { configureStore } from "@reduxjs/toolkit";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { beforeEach, describe, expect, it, vi } from "vitest";

import commonReducer from "@app/slices/commonSlice";
import searchReducer from "@app/slices/searchSlice";
import type { SearchQuery } from "@features/common/utils/model";

import { FolderView } from "./FolderView";

const { mockOpenQuery, mockSearchByFilename, mockSearchTree, translate } =
    vi.hoisted(() => ({
        mockOpenQuery: vi.fn(),
        mockSearchByFilename: vi.fn(),
        mockSearchTree: vi.fn(),
        // One function for the whole run, because the view takes `t` as an effect
        // dependency: a fresh one per render would re-run the filter on its own.
        translate: (key: string) => key,
    }));

vi.mock("@app/api/index", async (importOriginal) => ({
    ...(await importOriginal<typeof import("@app/api/index")>()),
    openFilenameSearchQuery: mockOpenQuery,
    searchByFilename: mockSearchByFilename,
    searchTree: mockSearchTree,
}));

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: translate }),
}));

/** What the left sidebar's global folder panel runs on: every file, no snapshot. */
const GLOBAL_FOLDER_QUERY: SearchQuery = {
    id: null,
    query: "*",
    keepAlive: null,
    sortField: null,
    sortDirection: null,
    sortId: null,
    pageSize: null,
};

const renderFolderView = (searchQuery: SearchQuery) =>
    render(
        <Provider
            store={configureStore({
                reducer: { search: searchReducer, common: commonReducer },
            })}
        >
            <FolderView searchQuery={searchQuery} />
        </Provider>,
    );

/** Type into the panel's own filter bar, which is where the text now lives. */
const typeFilter = (text: string) =>
    fireEvent.change(screen.getByLabelText("folderView.filterPlaceholder"), {
        target: { value: text },
    });

describe("the folder panel's filter", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockSearchTree.mockResolvedValue({ nodes: [], nextPageCursor: null });
        mockSearchByFilename.mockResolvedValue({ nodes: [], nextCursor: null });
        mockOpenQuery.mockResolvedValue({
            queryId: "opened-pit",
            keepAlive: "5m",
        });
    });

    it("opens a snapshot for a query that carries none", async () => {
        renderFolderView(GLOBAL_FOLDER_QUERY);

        typeFilter("report");

        await waitFor(() =>
            expect(mockSearchByFilename).toHaveBeenCalledWith(
                // The keep-alive travels with it: every request resets the
                // snapshot's life to the one it carries.
                { ...GLOBAL_FOLDER_QUERY, id: "opened-pit", keepAlive: "5m" },
                "report",
            ),
        );
    });

    it("opens its own snapshot even when the query carries one", async () => {
        // The search's snapshot is the result list's, and nothing reopens it from
        // here: a filter run reading it has no way back once it has expired.
        const searchBoundQuery: SearchQuery = {
            ...GLOBAL_FOLDER_QUERY,
            query: "invoice",
            id: "pit-1",
            keepAlive: "30m",
        };

        renderFolderView(searchBoundQuery);

        typeFilter("report");

        await waitFor(() =>
            expect(mockSearchByFilename).toHaveBeenCalledWith(
                { ...searchBoundQuery, id: "opened-pit", keepAlive: "5m" },
                "report",
            ),
        );
    });

    it("opens a fresh snapshot per search rather than holding one", async () => {
        // The tree beside the list is read live, so a snapshot held across searches
        // would filter an index the panel no longer shows.
        renderFolderView(GLOBAL_FOLDER_QUERY);

        typeFilter("rep");
        await waitFor(() => expect(mockOpenQuery).toHaveBeenCalledTimes(1));

        typeFilter("report");
        await waitFor(() => expect(mockOpenQuery).toHaveBeenCalledTimes(2));
    });

    it("keeps the filter bar when a search matches nothing", async () => {
        // The bar is the only way back out of a filter that found nothing, so the
        // panel has to go on rendering it when it has no rows to show.
        renderFolderView(GLOBAL_FOLDER_QUERY);

        typeFilter("nothing-matches-this");

        await waitFor(() => expect(mockSearchByFilename).toHaveBeenCalled());
        expect(
            screen.getByLabelText("folderView.filterPlaceholder"),
        ).toBeInTheDocument();
    });
});
