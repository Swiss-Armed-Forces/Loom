import { createListenerMiddleware, isAnyOf } from "@reduxjs/toolkit";
import {
    addCustomQuery,
    CUSTOM_QUERIES_LOCAL_STORAGE_KEY,
    deleteCustomQuery,
    fetchFilesCountForCustomQuery,
    markCustomQueryAsRead,
} from "../features/search/searchSlice";
import { RootState } from "./store";

export const localStorageCustomQueriesMiddleware = createListenerMiddleware();

localStorageCustomQueriesMiddleware.startListening({
    matcher: isAnyOf(
        addCustomQuery,
        deleteCustomQuery,
        markCustomQueryAsRead,
        fetchFilesCountForCustomQuery.fulfilled,
    ),
    effect: (_, listenerApi) => {
        const state = listenerApi.getState() as RootState;

        localStorage.setItem(
            CUSTOM_QUERIES_LOCAL_STORAGE_KEY,
            JSON.stringify(state.search.customQueries),
        );
    },
});
