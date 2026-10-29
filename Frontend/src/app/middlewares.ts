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
import { HIGHLIGHT_SETTLE_MS } from "@app/highlightSettle";
import {
    SEARCH_STATE_LOCAL_STORAGE_KEY,
    fetchPreview,
    selectAutoActionsPreferences,
    patchFilePreview,
    setHighlightedFileId,
    setPreviewFields,
} from "@app/slices/searchSlice";

import { RootState } from "./store";

interface CreateLocalStoragePersistListenerConfig {
    key: string;
    sliceName: string;
    fields: string[];
    debounceMs?: number;
}

export const createLocalStoragePersistListener = ({
    key,
    sliceName,
    fields,
    debounceMs = 500,
}: CreateLocalStoragePersistListenerConfig) => {
    const middleware = createListenerMiddleware();
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    middleware.startListening({
        predicate: () => true,
        effect: (_, listenerApi) => {
            if (debounceTimer) clearTimeout(debounceTimer);

            debounceTimer = setTimeout(() => {
                const state = listenerApi.getState() as Record<string, unknown>;
                const sliceState = state[sliceName] as Record<string, unknown>;

                if (!sliceState) return;

                let existing: Record<string, unknown> = {};
                const existingJson = localStorage.getItem(key);
                if (existingJson) {
                    try {
                        existing = JSON.parse(existingJson);
                    } catch {
                        // If parsing fails, start fresh
                    }
                }

                const persisted: Record<string, unknown> = { ...existing };
                for (const field of fields) {
                    if (field in sliceState) {
                        persisted[field] = sliceState[field];
                    }
                }

                localStorage.setItem(key, JSON.stringify(persisted));
            }, debounceMs);
        },
    });

    return middleware;
};

const PREVIEW_FIELDS_DEBOUNCE_MS = 300;

let previewFieldsDebounceTimer: ReturnType<typeof setTimeout> | null = null;
let autoActionsSettleTimer: ReturnType<typeof setTimeout> | null = null;
let lastAutoActionsFileId: string | null = null;
/** Auto-action writes still in flight, per file. See `runAutoActionsForFile`. */
const pendingAutoActions = new Map<string, Partial<GetFilePreviewResponse>>();

const runAutoActionsForFile = async (
    fileId: string,
    state: RootState,
    dispatch: (action: unknown) => void,
) => {
    const prefs = selectAutoActionsPreferences(state);
    const filePreview = state.search.files[fileId]?.preview;
    if (!filePreview) return;

    // isFirstRun guards the one-shot actions - the API scheduling calls and the
    // writes below - so they fire once per highlight session rather than on
    // every preview that arrives.
    const isFirstRun = lastAutoActionsFileId !== fileId;
    if (!isFirstRun) {
        // A preview that was already in flight when this file was opened can
        // land after the auto-action's own writes and describe the state from
        // before them. Re-assert what is still in flight, and only that: once
        // the writes have landed the server's answer is the truth, including
        // when the user has since changed the same flag by hand. Re-asserting
        // unconditionally would put `seen` back on every refetch without
        // telling the server, leaving the card and the server disagreeing for
        // good and "mark unread" impossible to see.
        const stillPending = pendingAutoActions.get(fileId);
        if (stillPending) {
            dispatch(patchFilePreview({ fileId, changes: stillPending }));
        }
        return;
    }

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
        scheduleSingleFileTranslation("", filePreview.fileId).catch(() => {});

    const optimisticUpdates: Partial<GetFilePreviewResponse> = {};
    const writes: Promise<unknown>[] = [];
    if (prefs.markAsSeen && !filePreview.seen) {
        optimisticUpdates.seen = true;
        writes.push(
            updateFile(filePreview.fileId, { seen: true }).catch((err) =>
                toast.error(
                    i18n.t("updateFileState.seen.scheduledErrorToast", { err }),
                ),
            ),
        );
    }
    if (prefs.flag && !filePreview.flagged) {
        optimisticUpdates.flagged = true;
        writes.push(
            updateFile(filePreview.fileId, { flagged: true }).catch((err) =>
                toast.error(
                    i18n.t("updateFileState.flagged.scheduledErrorToast", {
                        err,
                    }),
                ),
            ),
        );
    }
    if (Object.keys(optimisticUpdates).length > 0) {
        pendingAutoActions.set(fileId, optimisticUpdates);
        void Promise.allSettled(writes).then(() => {
            pendingAutoActions.delete(fileId);
        });
        dispatch(patchFilePreview({ fileId, changes: optimisticUpdates }));
    }
};

const SEARCH_PERSIST_FIELDS = [
    "query",
    "leftSidebarPanel",
    "rightSidebarTab",
    "leftSidebarWidth",
    "rightSidebarWidth",
    "openFileTabs",
    "followDetailTab",
    "customQueries",
    "expandFilePaths",
    "fieldLayout",
    "previewFields",
    "boldPreviewFields",
    "fieldColumnCount",
    "fieldColumnOf",
    "fieldColumnWidths",
    "thumbnailColumnWidth",
    "thumbnailWidthRem",
    "showHighlights",
    "showFieldNames",
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
    "folderViewOptions",
    "filteredFolderViewOptions",
    "bindings",
];

export const localStorageSearchStateMiddleware =
    createLocalStoragePersistListener({
        key: SEARCH_STATE_LOCAL_STORAGE_KEY,
        sliceName: "search",
        fields: SEARCH_PERSIST_FIELDS,
        debounceMs: 500,
    });

/**
 * Run auto-actions once the highlight has stopped moving.
 *
 * The file is resolved again when the timer fires rather than captured here:
 * what matters is the card the user ended up on, not every card they passed.
 */
const scheduleAutoActions = (
    getState: () => RootState,
    dispatch: (action: unknown) => void,
) => {
    if (autoActionsSettleTimer) clearTimeout(autoActionsSettleTimer);
    autoActionsSettleTimer = setTimeout(() => {
        autoActionsSettleTimer = null;
        const state = getState();
        const fileId = state.search.highlightedFileId;
        if (!fileId) return;
        void runAutoActionsForFile(fileId, state, dispatch);
    }, HIGHLIGHT_SETTLE_MS);
};

// Auto-actions when a file is highlighted (preview already in state)
localStorageSearchStateMiddleware.startListening({
    actionCreator: setHighlightedFileId,
    effect: (action, listenerApi) => {
        if (!action.payload) {
            if (autoActionsSettleTimer) clearTimeout(autoActionsSettleTimer);
            autoActionsSettleTimer = null;
            lastAutoActionsFileId = null;
            return;
        }
        scheduleAutoActions(
            () => listenerApi.getState() as RootState,
            listenerApi.dispatch,
        );
    },
});

// Auto-actions when preview loads for an already-highlighted file. Goes through
// the same settle timer, so a preview landing mid-scroll cannot mark a card the
// highlight is about to leave.
localStorageSearchStateMiddleware.startListening({
    actionCreator: fetchPreview.fulfilled,
    effect: (action, listenerApi) => {
        const state = listenerApi.getState() as RootState;
        const highlightedId = state.search.highlightedFileId;
        if (highlightedId && action.payload?.preview.fileId === highlightedId) {
            scheduleAutoActions(
                () => listenerApi.getState() as RootState,
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
