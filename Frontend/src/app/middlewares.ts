import { createListenerMiddleware } from "@reduxjs/toolkit";

import { SEARCH_STATE_LOCAL_STORAGE_KEY } from "@app/slices/searchSlice";

import { RootState } from "./store";

let persistDebounceTimer: ReturnType<typeof setTimeout> | null = null;

export const localStorageSearchStateMiddleware = createListenerMiddleware();

localStorageSearchStateMiddleware.startListening({
    predicate: () => true,
    effect: (_, listenerApi) => {
        if (persistDebounceTimer) clearTimeout(persistDebounceTimer);
        persistDebounceTimer = setTimeout(() => {
            const state = (listenerApi.getState() as RootState).search;
            localStorage.setItem(
                SEARCH_STATE_LOCAL_STORAGE_KEY,
                JSON.stringify(state),
            );
        }, 500);
    },
});
