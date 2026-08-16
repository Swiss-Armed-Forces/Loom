import { createListenerMiddleware } from "@reduxjs/toolkit";
import i18n from "i18next";
import { toast } from "react-toastify";

import {
    GetFilePreviewResponse,
    scheduleSingleFileIndexing,
    scheduleSingleFileSummarization,
    scheduleSingleFileTranslation,
    scheduleSingleImageDescription,
    updateFile,
} from "@app/api";
import {
    SEARCH_STATE_LOCAL_STORAGE_KEY,
    fetchPreview,
    selectAutoActionsPreferences,
    setFilePreview,
    setHighlightedFileId,
    setPreviewFields,
} from "@app/slices/searchSlice";

import { RootState } from "./store";

const PREVIEW_FIELDS_DEBOUNCE_MS = 300;

let persistDebounceTimer: ReturnType<typeof setTimeout> | null = null;
let previewFieldsDebounceTimer: ReturnType<typeof setTimeout> | null = null;
let lastAutoActionsFileId: string | null = null;

const runAutoActionsForFile = async (
    fileId: string,
    state: RootState,
    dispatch: (action: unknown) => void,
) => {
    const prefs = selectAutoActionsPreferences(state);
    const filePreview = state.search.files[fileId]?.preview;
    if (!filePreview) return;

    // isFirstRun guards one-shot actions (API scheduling calls) that must only
    // fire once per highlight session. The optimistic state dispatch below is
    // NOT guarded — it must re-apply on every fetchPreview.fulfilled so that a
    // re-fetch triggered by setFileInViewState (which sees cachedQuery !== activeQuery
    // for temporary/out-of-results files) doesn't permanently overwrite seen/flagged.
    const isFirstRun = lastAutoActionsFileId !== fileId;
    if (isFirstRun) {
        lastAutoActionsFileId = fileId;
        if (prefs.reindex)
            scheduleSingleFileIndexing(filePreview.fileId).catch(() => {});
        if (prefs.summarize)
            scheduleSingleFileSummarization(filePreview.fileId, null).catch(
                () => {},
            );
        if (prefs.describeImage)
            scheduleSingleImageDescription(filePreview.fileId, null).catch(
                () => {},
            );
        if (prefs.translate)
            scheduleSingleFileTranslation("", filePreview.fileId).catch(
                () => {},
            );
    }

    const optimisticUpdates: Partial<GetFilePreviewResponse> = {};
    if (prefs.markAsSeen && !filePreview.seen) {
        if (isFirstRun) {
            updateFile(filePreview.fileId, { seen: true }).catch((err) =>
                toast.error(
                    i18n.t("updateFileState.seen.scheduledErrorToast", { err }),
                ),
            );
        }
        optimisticUpdates.seen = true;
    }
    if (prefs.flag && !filePreview.flagged) {
        if (isFirstRun) {
            updateFile(filePreview.fileId, { flagged: true }).catch((err) =>
                toast.error(
                    i18n.t("updateFileState.flagged.scheduledErrorToast", {
                        err,
                    }),
                ),
            );
        }
        optimisticUpdates.flagged = true;
    }
    if (Object.keys(optimisticUpdates).length > 0) {
        dispatch(setFilePreview({ ...filePreview, ...optimisticUpdates }));
    }
};

export const localStorageSearchStateMiddleware = createListenerMiddleware();

localStorageSearchStateMiddleware.startListening({
    predicate: () => true,
    effect: (_, listenerApi) => {
        if (persistDebounceTimer) clearTimeout(persistDebounceTimer);
        persistDebounceTimer = setTimeout(() => {
            const state = (listenerApi.getState() as RootState).search;
            const persistedKeys = new Set([
                "query",
                "leftSidebarPanel",
                "rightSidebarTab",
                "openFileTabs",
                "activeTabFileId",
                "customQueries",
                "expandFilePaths",
                "cardDensity",
                "previewFields",
                "showThumbnails",
                "showHighlights",
                "showFieldSections",
                "showExtensionIcon",
                "showFilePath",
                "showParentNavigation",
                "showStatusIndicators",
                "showAttachments",
                "showTags",
                "showActions",
                "showSortIndicator",
                "showFieldActions",
                "autoActionsPreferences",
                "suppressDownloadWarning",
                "summarizationSystemPrompt",
                "visionSystemPrompt",
                "displayStat",
                "displayHistogramStat",
                "folderViewExpandedNodes",
                "filteredFolderViewExpandedNodes",
            ]);
            const persisted: Record<string, unknown> = {};
            for (const key of persistedKeys) {
                if (key in state) {
                    persisted[key] = state[key as keyof typeof state];
                }
            }
            localStorage.setItem(
                SEARCH_STATE_LOCAL_STORAGE_KEY,
                JSON.stringify(persisted),
            );
        }, 500);
    },
});

// Auto-actions when a file is highlighted (preview already in state)
localStorageSearchStateMiddleware.startListening({
    actionCreator: setHighlightedFileId,
    effect: async (action, listenerApi) => {
        const fileId = action.payload;
        if (!fileId) {
            lastAutoActionsFileId = null;
            return;
        }
        await runAutoActionsForFile(
            fileId,
            listenerApi.getState() as RootState,
            listenerApi.dispatch,
        );
    },
});

// Auto-actions when preview loads for an already-highlighted file
localStorageSearchStateMiddleware.startListening({
    actionCreator: fetchPreview.fulfilled,
    effect: async (action, listenerApi) => {
        const state = listenerApi.getState() as RootState;
        const highlightedId = state.search.highlightedFileId;
        if (highlightedId && action.payload?.preview.fileId === highlightedId) {
            await runAutoActionsForFile(
                highlightedId,
                state,
                listenerApi.dispatch,
            );
        }
    },
});

// Re-fetch all in-view previews when the selected preview fields change so
// cards immediately reflect the new field set.
// Pass the active query explicitly so the thunk never falls back to "hidden:*"
// for files that happen to have a null meta (e.g. temporary card, stale entry).
// Also skip file IDs that are no longer present in search.files.
localStorageSearchStateMiddleware.startListening({
    actionCreator: setPreviewFields,
    effect: (_, listenerApi) => {
        if (previewFieldsDebounceTimer)
            clearTimeout(previewFieldsDebounceTimer);
        previewFieldsDebounceTimer = setTimeout(() => {
            const { filesInView, files, query } = (
                listenerApi.getState() as RootState
            ).search;
            for (const fileId of filesInView) {
                if (fileId in files) {
                    listenerApi.dispatch(
                        fetchPreview({ fileId, query: query ?? undefined }),
                    );
                }
            }
        }, PREVIEW_FIELDS_DEBOUNCE_MS);
    },
});
