import { createListenerMiddleware, isAnyOf } from "@reduxjs/toolkit";

import {
    addCustomQuery,
    AUTO_ACTIONS_PREFERENCES_LOCAL_STORAGE_KEY,
    CUSTOM_QUERIES_LOCAL_STORAGE_KEY,
    deleteCustomQuery,
    fetchFilesCountForCustomQuery,
    markCustomQueryAsRead,
    setAutoActionPreference,
    SIDE_MENU_LOCAL_STORAGE_KEY,
    toggleSideMenu,
    toggleSideMenuAutoActions,
    toggleSideMenuBulkActions,
    toggleSideMenuTags,
    toggleSideMenuQueries,
} from "@app/slices/searchSlice";

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

export const localStorageAutoActionsMiddleware = createListenerMiddleware();

localStorageAutoActionsMiddleware.startListening({
    matcher: isAnyOf(setAutoActionPreference),
    effect: (_, listenerApi) => {
        const state = listenerApi.getState() as RootState;

        localStorage.setItem(
            AUTO_ACTIONS_PREFERENCES_LOCAL_STORAGE_KEY,
            JSON.stringify(state.search.autoActionsPreferences),
        );
    },
});

export const localStorageSideMenuMiddleware = createListenerMiddleware();

localStorageSideMenuMiddleware.startListening({
    matcher: isAnyOf(
        toggleSideMenu,
        toggleSideMenuBulkActions,
        toggleSideMenuTags,
        toggleSideMenuQueries,
        toggleSideMenuAutoActions,
    ),
    effect: (_, listenerApi) => {
        const state = listenerApi.getState() as RootState;

        localStorage.setItem(
            SIDE_MENU_LOCAL_STORAGE_KEY,
            JSON.stringify(state.search.sideMenu),
        );
    },
});
