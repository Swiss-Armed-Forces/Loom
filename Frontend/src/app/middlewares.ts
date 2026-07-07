import { createListenerMiddleware, isAnyOf } from "@reduxjs/toolkit";

import {
    addCustomQuery,
    AUTO_ACTIONS_PREFERENCES_LOCAL_STORAGE_KEY,
    closeFileTab,
    CUSTOM_QUERIES_LOCAL_STORAGE_KEY,
    deleteCustomQuery,
    fetchFilesCountForCustomQuery,
    markCustomQueryAsRead,
    openFileTab,
    setAutoActionPreference,
    setExpandFilePaths,
    setFileTabDetailTab,
    setLeftSidebarPanel,
    setRightSidebarTab,
    toggleRightSidebar,
    UI_STATE_LOCAL_STORAGE_KEY,
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

export const localStorageUiStateMiddleware = createListenerMiddleware();

localStorageUiStateMiddleware.startListening({
    matcher: isAnyOf(
        setLeftSidebarPanel,
        setRightSidebarTab,
        toggleRightSidebar,
        openFileTab,
        closeFileTab,
        setFileTabDetailTab,
        setExpandFilePaths,
    ),
    effect: (_, listenerApi) => {
        const state = listenerApi.getState() as RootState;
        localStorage.setItem(
            UI_STATE_LOCAL_STORAGE_KEY,
            JSON.stringify({
                leftSidebarPanel: state.search.leftSidebarPanel,
                rightSidebarOpen: state.search.rightSidebarOpen,
                rightSidebarTab: state.search.rightSidebarTab,
                openFileTabs: state.search.openFileTabs,
                expandFilePaths: state.search.expandFilePaths,
            }),
        );
    },
});
