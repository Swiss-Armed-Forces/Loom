import { createListenerMiddleware, isAnyOf } from "@reduxjs/toolkit";

import {
    addCustomQuery,
    AUTO_ACTIONS_PREFERENCES_LOCAL_STORAGE_KEY,
    closeFileTab,
    CUSTOM_QUERIES_LOCAL_STORAGE_KEY,
    deleteCustomQuery,
    fetchFilesCountForCustomQuery,
    FOLDER_VIEW_EXPANDED_NODES_LOCAL_STORAGE_KEY,
    HIGHLIGHTED_FILE_ID_LOCAL_STORAGE_KEY,
    markCustomQueryAsRead,
    openFileTab,
    selectOrderedFileIds,
    setAutoActionPreference,
    setExpandFilePaths,
    setFileTabDetailTab,
    setFolderViewExpandedNodes,
    setHighlightedIndex,
    setLeftSidebarPanel,
    setRightSidebarTab,
    setDisplayHistogramStat,
    setDisplayStat,
    setSuppressDownloadWarning,
    STATS_STATE_LOCAL_STORAGE_KEY,
    SUPPRESS_DOWNLOAD_WARNING_LOCAL_STORAGE_KEY,
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

export const localStorageSuppressDownloadWarningMiddleware =
    createListenerMiddleware();

localStorageSuppressDownloadWarningMiddleware.startListening({
    matcher: isAnyOf(setSuppressDownloadWarning),
    effect: (_, listenerApi) => {
        const state = listenerApi.getState() as RootState;
        localStorage.setItem(
            SUPPRESS_DOWNLOAD_WARNING_LOCAL_STORAGE_KEY,
            JSON.stringify(state.search.suppressDownloadWarning),
        );
    },
});

export const localStorageHighlightedFileIdMiddleware =
    createListenerMiddleware();

localStorageHighlightedFileIdMiddleware.startListening({
    matcher: isAnyOf(setHighlightedIndex),
    effect: (_, listenerApi) => {
        const state = listenerApi.getState() as RootState;
        const index = state.search.keyboardNavigation.highlightedIndex;
        const orderedFileIds = selectOrderedFileIds(state);
        const fileId = index !== null ? (orderedFileIds[index] ?? null) : null;
        localStorage.setItem(
            HIGHLIGHTED_FILE_ID_LOCAL_STORAGE_KEY,
            JSON.stringify(fileId),
        );
    },
});

export const localStorageFolderViewExpandedNodesMiddleware =
    createListenerMiddleware();

localStorageFolderViewExpandedNodesMiddleware.startListening({
    matcher: isAnyOf(setFolderViewExpandedNodes),
    effect: (_, listenerApi) => {
        const state = listenerApi.getState() as RootState;
        localStorage.setItem(
            FOLDER_VIEW_EXPANDED_NODES_LOCAL_STORAGE_KEY,
            JSON.stringify(state.search.folderViewExpandedNodes),
        );
    },
});

export const localStorageStatsStateMiddleware = createListenerMiddleware();

localStorageStatsStateMiddleware.startListening({
    matcher: isAnyOf(setDisplayStat, setDisplayHistogramStat),
    effect: (_, listenerApi) => {
        const state = listenerApi.getState() as RootState;
        localStorage.setItem(
            STATS_STATE_LOCAL_STORAGE_KEY,
            JSON.stringify({
                displayStat: state.search.displayStat,
                displayHistogramStat: state.search.displayHistogramStat,
            }),
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
