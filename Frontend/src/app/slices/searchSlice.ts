import {
    AsyncThunkConfig,
    createAsyncThunk,
    createSelector,
    createSlice,
    GetThunkAPI,
    PayloadAction,
} from "@reduxjs/toolkit";
import { t } from "i18next";
import { toast } from "react-toastify";
import { v4 as uuidv4 } from "uuid";

import {
    getFilePreview,
    GetFilePreviewResponse,
    searchFiles,
    GroupedHistogramStatisticsModel,
    TermsStatisticsModel,
    AvailableStat,
    PubSubMessage,
    getLongRunningQuery,
    getFilesCount,
    ResponseError,
    PreviewField,
} from "@app/api/index";
import {
    subscribeChannel,
    unsubscribeChannel,
} from "@app/channelSubscriptions";
import {
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import { isLoadedResult, SearchFileEntry } from "@app/slices/searchFileEntry";
import { FileDetailTab } from "@features/common/utils/enums";
import {
    CombinedStats,
    PitBoundSearchQuery,
    SearchQuery,
} from "@features/common/utils/model";
import { shortcutRegistry } from "@features/search/hooks/shortcutRegistry";
import {
    DEFAULT_HISTOGRAM_STAT,
    DEFAULT_TERMS_STAT,
} from "@features/search/views/Statistics/statOrder";
import { webSocketSendMessage } from "@middleware/SocketMiddleware";

import { RootState } from "../store";

export const LeftSidebarPanel = {
    FOLDER: "folder",
    TAGS: "tags",
    QUERIES: "queries",
    CUSTOMIZATION: "customization",
    CHAT: "chat",
} as const;

export type LeftSidebarPanel =
    (typeof LeftSidebarPanel)[keyof typeof LeftSidebarPanel];

export const RightSidebarTab = {
    BULK_ACTIONS: "bulk_actions",
    FOLDER: "folder_scoped",
    STATISTICS: "statistics",
    CHAT: "chat",
    FILE_DETAIL: "file_detail",
} as const;

export type RightSidebarTab =
    (typeof RightSidebarTab)[keyof typeof RightSidebarTab];

/** How much room a card takes: a named spacing, or one picked from the width
 *  available. Spacing is one axis of the card's look; which elements are on is
 *  the other, and the two are set independently - see `DENSITY_PRESETS`. */
export type CardDensity = "auto" | NamedDensity;
export type NamedDensity = "compact" | "standard" | "full";

/** How a single metadata field is rendered on a card.
 *  "rows" → one expandable accordion per field; "compact" → one `label: value`
 *  line per field, with the accordion kept for truncated values only;
 *  "line" → every selected field side by side on one line, values only, the
 *  way a mail client lays a message list out. */
export type FieldLayout = "rows" | "compact" | "line";

// All card-element visibility settings in one shape, shared by presets and state.
export interface CardVisibilitySettings {
    showThumbnails: boolean;
    showHighlights: boolean;
    showFieldSections: boolean;
    showExtensionIcon: boolean;
    showFilePath: boolean;
    showParentNavigation: boolean;
    showStatusIndicators: boolean;
    showAttachments: boolean;
    showTags: boolean;
    showActions: boolean;
    showSortIndicator: boolean;
    showFieldActions: boolean;
}

export const DENSITY_PRESETS: Record<NamedDensity, CardVisibilitySettings> = {
    compact: {
        showThumbnails: false,
        showHighlights: false,
        showFieldSections: true,
        showExtensionIcon: true,
        showFilePath: true,
        showParentNavigation: false,
        showStatusIndicators: false,
        showAttachments: false,
        showTags: false,
        showActions: false,
        showSortIndicator: false,
        showFieldActions: false,
    },
    standard: {
        showThumbnails: false,
        showHighlights: true,
        showFieldSections: true,
        showExtensionIcon: true,
        showFilePath: true,
        showParentNavigation: true,
        showStatusIndicators: true,
        showAttachments: true,
        showTags: true,
        showActions: false,
        showSortIndicator: false,
        showFieldActions: true,
    },
    full: {
        showThumbnails: true,
        showHighlights: true,
        showFieldSections: true,
        showExtensionIcon: true,
        showFilePath: true,
        showParentNavigation: true,
        showStatusIndicators: true,
        showAttachments: true,
        showTags: true,
        showActions: true,
        showSortIndicator: true,
        showFieldActions: true,
    },
};

/** The flags a preset sets, named once so state and preset can be compared
 *  without listing them again. */
export const CARD_VISIBILITY_KEYS = Object.keys(
    DENSITY_PRESETS.standard,
) as (keyof CardVisibilitySettings)[];

const matchesPreset = (
    visibility: CardVisibilitySettings,
    preset: CardVisibilitySettings,
): boolean =>
    CARD_VISIBILITY_KEYS.every((key) => visibility[key] === preset[key]);

export interface FileTabState {
    fileId: string;
    detailTab: FileDetailTab;
}

export interface CustomQuery {
    id: string;
    query: SearchQuery;
    fileCount: number;
    // Baseline the "new files" badge compares against. It only ever moves when
    // the user opens the query (markCustomQueryAsRead); a poll reporting a
    // *lower* count must not move it, or deleting files silently rebaselines
    // and hides subsequent genuine matches.
    lastSeenCount: number;
    hasNewFiles: boolean;
    name: string;
    icon: string;
}

export const initCustomQuery = (
    query: SearchQuery,
    fileCount: number,
    name: string,
    icon: string,
): CustomQuery => {
    return {
        id: uuidv4(),
        query,
        fileCount,
        lastSeenCount: fileCount,
        hasNewFiles: false,
        name,
        icon,
    };
};

/**
 * Coerce persisted saved queries back into the current shape.
 *
 * `loadPersistedSearchState` is a bare `JSON.parse` cast, so entries written
 * before `lastSeenCount` existed arrive without it. Seeding the baseline from
 * `fileCount` is what stops every existing browser lighting up every badge on
 * the first load after deploy.
 */
export const normalizeCustomQueries = (raw: unknown): CustomQuery[] => {
    if (!Array.isArray(raw)) return [];
    return raw.flatMap((entry): CustomQuery[] => {
        if (entry === null || typeof entry !== "object") return [];
        const candidate = entry as Partial<CustomQuery>;
        if (
            typeof candidate.id !== "string" ||
            typeof candidate.name !== "string" ||
            candidate.query === null ||
            typeof candidate.query !== "object"
        ) {
            return [];
        }
        const fileCount =
            typeof candidate.fileCount === "number" ? candidate.fileCount : 0;
        return [
            {
                id: candidate.id,
                query: candidate.query,
                fileCount,
                lastSeenCount:
                    typeof candidate.lastSeenCount === "number"
                        ? candidate.lastSeenCount
                        : fileCount,
                hasNewFiles: candidate.hasNewFiles === true,
                name: candidate.name,
                icon: typeof candidate.icon === "string" ? candidate.icon : "",
            },
        ];
    });
};

export interface AutoActionsPreferences {
    markAsSeen: boolean;
    flag: boolean;
    reindex: boolean;
    translate: boolean;
    summarize: boolean;
    describeImage: boolean;
}

export interface SearchState {
    query: SearchQuery | null;
    queryError?: string;
    leftSidebarPanel: LeftSidebarPanel | null;
    rightSidebarTab: RightSidebarTab | null;
    stats: CombinedStats;
    bindings: Record<string, string[]>;
    files: {
        [fileId: string]: SearchFileEntry;
    };
    temporaryFileId: string | null;
    totalFiles: number;
    lastFileSortId: any[] | null;
    filesInView: string[];
    tags: string[];
    customQueries: CustomQuery[];
    highlightedQueryId: string | null;
    openFileTabs: FileTabState[];
    activeTabFileId: string | null;
    expandFilePaths: boolean;
    cardDensity: CardDensity;
    autoDetectedDensity: NamedDensity;
    fieldLayout: FieldLayout;
    previewFields: string[];
    fieldColumnWidths: Record<string, number>;
    thumbnailColumnWidth: number | null;
    availablePreviewFields: PreviewField[];
    fieldExpansion: Record<string, boolean>;
    showThumbnails: boolean;
    showHighlights: boolean;
    showFieldSections: boolean;
    showExtensionIcon: boolean;
    showFilePath: boolean;
    showParentNavigation: boolean;
    showStatusIndicators: boolean;
    showAttachments: boolean;
    showTags: boolean;
    showActions: boolean;
    showSortIndicator: boolean;
    showFieldActions: boolean;
    autoActionsPreferences: AutoActionsPreferences;
    contentTruncatedFilesCount: number;
    attachmentsSkippedFilesCount: number;
    failedFilesCount: number;
    displayStat: string;
    displayHistogramStat: string;
    termsStats: AvailableStat[];
    histogramStats: AvailableStat[];
    webSocketPubSubMessage: PubSubMessage | null;
    summarizationSystemPrompt: string | null;
    visionSystemPrompt: string | null;
    highlightedFileId: string | null;
    highlightScrollRequest: number;
    highlightScrollMode: "smart" | "top";
    suppressDownloadWarning: boolean;
    folderViewExpandedNodes: string[];
    filteredFolderViewExpandedNodes: string[];
    pendingFullscreenFileId: string | null;
    showChatReasoning: boolean;
}

export const SEARCH_STATE_DOCS = {
    query: "SearchQuery | null — active search query (text, filters, sort)",
    queryError: "string | undefined — validation error for the current query",
    leftSidebarPanel:
        "LeftSidebarPanel | null — active left sidebar panel (folder/tags/queries/card_customization/chat)",
    rightSidebarTab: "RightSidebarTab | null — active right sidebar tab",
    stats: "CombinedStats — search statistics (termsData, histogramData)",
    files: "Record<fileId, {meta, preview, query, stale?, temporary?}> — file entry cache: search hits (meta set) plus entries kept for open tabs, fetched previews and the temporary highlight (meta null), so the key count is not the number of results shown",
    temporaryFileId:
        "string | null — ID of a transiently opened file not in search results",
    totalFiles: "number — total result count for the current query",
    lastFileSortId: "any[] | null — sort cursor for pagination",
    filesInView: "string[] — ordered file IDs visible in the result list",
    tags: "string[] — available tags",
    customQueries:
        "CustomQuery[] — saved queries ({id, query, fileCount, lastSeenCount, hasNewFiles, name, icon})",
    highlightedQueryId:
        "string | null — which custom query is highlighted in the sidebar",
    openFileTabs:
        "FileTabState[] — open file detail tabs ({fileId, detailTab})",
    activeTabFileId: "string | null — which file detail tab is active",
    expandFilePaths:
        "boolean — whether long file paths are shown in full on every result card",
    cardDensity:
        "CardDensity — how much room a card takes (auto|compact|standard|full); which elements are shown is the separate show* set",
    autoDetectedDensity:
        "NamedDensity — spacing detected from available screen space, used while cardDensity is auto",
    fieldLayout:
        "FieldLayout — how card metadata fields are rendered (rows|compact|line)",
    previewFields: "string[] — field names shown as preview on cards",
    fieldColumnWidths:
        "Record<fieldName, number> — width in fr of each column in the line field layout, as left by dragging the column borders; a field absent from the map is one that was never dragged",
    thumbnailColumnWidth:
        "number | null — edge length in px of the thumbnail column in the line field layout, as left by dragging its border; null means the density decides",
    availablePreviewFields:
        "PreviewField[] — all fields available for card preview",
    fieldExpansion:
        "Record<fieldName, boolean> — which card field sections are expanded",
    showThumbnails: "boolean — card visibility: thumbnail images",
    showHighlights: "boolean — card visibility: search hit highlights",
    showFieldSections: "boolean — card visibility: metadata field sections",
    showExtensionIcon: "boolean — card visibility: file extension icon",
    showFilePath: "boolean — card visibility: file path",
    showParentNavigation: "boolean — card visibility: parent folder navigation",
    showStatusIndicators:
        "boolean — card visibility: processing status indicators",
    showAttachments: "boolean — card visibility: attachment list",
    showTags: "boolean — card visibility: tag chips",
    showActions: "boolean — card visibility: action buttons",
    showSortIndicator: "boolean — card visibility: sort field indicator",
    showFieldActions: "boolean — card visibility: per-field action buttons",
    autoActionsPreferences:
        "AutoActionsPreferences — which auto-actions run on file open (markAsSeen, flag, reindex, translate, summarize, describeImage)",
    contentTruncatedFilesCount:
        "number — files with truncated content in current results",
    attachmentsSkippedFilesCount:
        "number — files with skipped attachments in current results",
    failedFilesCount:
        "number — files that failed processing in current results",
    displayStat: "string — which terms stat is shown in the statistics panel",
    displayHistogramStat:
        "string — which histogram stat is shown in the statistics panel",
    termsStats: "AvailableStat[] — available term aggregation statistics",
    histogramStats: "AvailableStat[] — available histogram statistics",
    webSocketPubSubMessage:
        "PubSubMessage | null — last received WebSocket pub/sub message",
    summarizationSystemPrompt:
        "string | null — custom system prompt for summarization",
    visionSystemPrompt:
        "string | null — custom system prompt for vision/image description",
    highlightedFileId:
        "string | null — file card currently focused/highlighted",
    highlightScrollRequest:
        "number — counter incremented to trigger scroll to highlighted file",
    highlightScrollMode:
        '"smart" | "top" — scroll behaviour when highlighting a file',
    suppressDownloadWarning:
        "boolean — whether the download size warning dialog is suppressed",
    folderViewExpandedNodes: "string[] — expanded node IDs in the folder tree",
    filteredFolderViewExpandedNodes:
        "string[] — expanded node IDs in the filtered folder tree",
    pendingFullscreenFileId:
        "string | null — file ID queued to open in fullscreen",
    showChatReasoning:
        "boolean — whether AI chat reasoning/thinking output is expanded",
    bindings:
        "Record<string, string[]> — custom keyboard shortcut bindings (actionId → keys)",
} satisfies Record<keyof SearchState, string>;

export const QUERY_FAILED_FILES = "state:failed";
export const QUERY_CONTENT_TRUNCATED_FILES = "content_truncated:true";
export const QUERY_ATTACHMENTS_SKIPPED_FILES = "attachments_skipped:true";

export const SEARCH_STATE_LOCAL_STORAGE_KEY = "SEARCH_STATE";

/**
 * Coerce a persisted card density back into the current shape.
 *
 * Browsers that were left on the "custom" density hold a value the union no
 * longer has. They are handed back to "auto": the switches they customised
 * are now always in effect, so the only thing "custom" still had to say was
 * that it was not a preset - and nothing is lost by letting the spacing
 * follow the window again.
 */
const normalizeCardDensity = (raw: unknown): CardDensity | undefined => {
    if (
        raw === "auto" ||
        raw === "compact" ||
        raw === "standard" ||
        raw === "full"
    ) {
        return raw;
    }
    return raw === undefined ? undefined : "auto";
};

export const loadPersistedSearchState = (): Partial<SearchState> => {
    const data = window.localStorage.getItem(SEARCH_STATE_LOCAL_STORAGE_KEY);
    if (!data) return {};
    try {
        const parsed = JSON.parse(data) as Partial<SearchState>;
        const density = normalizeCardDensity(parsed.cardDensity);
        return {
            ...parsed,
            ...(density ? { cardDensity: density } : {}),
            ...("customQueries" in parsed
                ? {
                      customQueries: normalizeCustomQueries(
                          parsed.customQueries,
                      ),
                  }
                : {}),
        };
    } catch {
        return {};
    }
};

const persistedState = loadPersistedSearchState();
// Seed activeTabFileId from the URL hash so the Redux→URL effect sees a match
// on initial mount and doesn't clear the hash before the URL→Redux effect can
// open the tab. The URL→Redux effect (syncedHashRef = "") still fires and calls
// openFileTabThunk to ensure the tab is added to openFileTabs if it isn't yet.
const initialHashFileId = window.location.hash.substring(1) || null;

const initialState: SearchState = {
    leftSidebarPanel: null,
    rightSidebarTab: null,
    stats: { termsData: null, histogramData: null },
    files: {},
    lastFileSortId: null,
    totalFiles: 0,
    filesInView: [],
    tags: [],
    customQueries: [],
    highlightedQueryId: null,
    openFileTabs: [],
    expandFilePaths: false,
    cardDensity: "auto",
    autoDetectedDensity: "standard",
    fieldLayout: "compact",
    previewFields: ["content"],
    fieldColumnWidths: {},
    thumbnailColumnWidth: null,
    availablePreviewFields: [],
    // The element switches, always authoritative; they start from standard.
    ...DENSITY_PRESETS.standard,
    fieldExpansion: {},
    autoActionsPreferences: {
        markAsSeen: true,
        flag: false,
        reindex: false,
        translate: false,
        summarize: false,
        describeImage: false,
    },
    contentTruncatedFilesCount: 0,
    attachmentsSkippedFilesCount: 0,
    failedFilesCount: 0,
    displayStat: DEFAULT_TERMS_STAT,
    displayHistogramStat: DEFAULT_HISTOGRAM_STAT,
    termsStats: [],
    histogramStats: [],
    webSocketPubSubMessage: null,
    summarizationSystemPrompt: null,
    visionSystemPrompt: null,
    highlightedFileId: null,
    highlightScrollRequest: 0,
    highlightScrollMode: "smart" as const,
    temporaryFileId: null,
    suppressDownloadWarning: false,
    folderViewExpandedNodes: [],
    filteredFolderViewExpandedNodes: [],
    pendingFullscreenFileId: null,
    showChatReasoning: false,
    bindings: {},
    ...persistedState,
    // Restore the last query (text + sort) so stale data renders immediately.
    // Strip sortId (pagination cursor) so the first real fetch starts from page 1.
    // activeTabFileId always comes from the URL hash.
    query: persistedState.query
        ? { ...(persistedState.query as SearchQuery), sortId: null }
        : null,
    activeTabFileId: initialHashFileId,
} as SearchState;

export const updateQuery = createAsyncThunk(
    "updateQueryThunk",
    async (query: Partial<SearchQuery>, thunkAPI) => {
        const dispatch = thunkAPI.dispatch;
        const { search } = thunkAPI.getState() as RootState;
        const lastQuery = search.query;

        const queryId = query.id ?? (await getLongRunningQuery()).queryId;
        if (thunkAPI.signal.aborted) return;
        const queryQuery = query.query ?? lastQuery?.query ?? "";

        if (!queryQuery.trim()) {
            return;
        }

        const newQuery: PitBoundSearchQuery = {
            id: queryId,
            query: queryQuery,
            keepAlive: query.keepAlive ?? lastQuery?.keepAlive ?? null,
            sortField:
                query.sortField !== undefined
                    ? query.sortField?.trim() || null
                    : (lastQuery?.sortField ?? null),
            sortDirection:
                query.sortDirection ?? lastQuery?.sortDirection ?? null,
            sortId: query.sortId ?? null,
            pageSize: query.pageSize ?? null,
        };
        const queryIdChanged = lastQuery?.id !== queryId;
        let querySubscriptionActive = queryIdChanged;
        const cleanupQuerySubscription = () => {
            if (!querySubscriptionActive) return;
            querySubscriptionActive = false;
            dispatch(
                webSocketSendMessage({
                    message: {
                        type: "unsubscribe",
                        channels: new Set([queryId]),
                    },
                }),
            );
        };
        const handleAbort = () => {
            cleanupQuerySubscription();
            dispatch(stopLoadingIndicator());
        };

        dispatch(startLoadingIndicator());

        if (queryIdChanged) {
            dispatch(
                webSocketSendMessage({
                    message: {
                        type: "subscribe",
                        channels: new Set([queryId]),
                    },
                }),
            );
        }
        thunkAPI.signal.addEventListener("abort", handleAbort, { once: true });
        try {
            const [searchRes, countRes] = await Promise.all([
                searchFiles(newQuery),
                getFilesCount(newQuery),
            ]);
            if (thunkAPI.signal.aborted) return;

            if (queryIdChanged && lastQuery?.id) {
                dispatch(
                    webSocketSendMessage({
                        message: {
                            type: "unsubscribe",
                            channels: new Set([lastQuery.id]),
                        },
                    }),
                );
            }

            return { ...searchRes, ...countRes, query: newQuery };
        } catch (error: any) {
            if (thunkAPI.signal.aborted) return;
            cleanupQuerySubscription();
            // 409 means the point-in-time this query was paging against has expired.
            // Pages cannot be resumed across snapshots, so the only correct recovery
            // is a fresh snapshot read from the first page: drop the id so a new one
            // is opened, and the sortId that pointed into the old one.
            //
            // Retried only when the caller supplied the id — "load more" does, and
            // that is the request that outlives a snapshot. The retry carries no id,
            // so a 409 on a snapshot opened moments earlier surfaces as the real
            // error it is instead of looping.
            if (
                error instanceof ResponseError &&
                error.response.status === 409 &&
                query.id !== undefined
            ) {
                toast.info(t("generalSearchView.queryExpired"));
                dispatch(
                    updateQuery({ ...query, id: undefined, sortId: null }),
                );
                return;
            }
            // Get error detail
            let errorDetail = error.toString();
            if (error instanceof ResponseError) {
                const errorData = await error.response.json();
                errorDetail = errorData?.detail ?? JSON.stringify(errorData);
            }
            return thunkAPI.rejectWithValue(errorDetail);
        } finally {
            thunkAPI.signal.removeEventListener("abort", handleAbort);
            if (!thunkAPI.signal.aborted) dispatch(stopLoadingIndicator());
        }
    },
);

export const fetchPreview = createAsyncThunk(
    "fetchPreviewThunk",
    async (
        {
            fileId,
            query,
        }: {
            fileId: string;
            query?: SearchQuery;
        },
        thunkAPI: GetThunkAPI<AsyncThunkConfig>,
    ) => {
        const { search } = thunkAPI.getState() as RootState;
        // Stale files are fetched without any query context so they load via
        // "hidden:*" unconditionally — their stored query no longer matches.
        // For non-stale files: use the explicit query if provided, otherwise
        // fall back to the active search query only when the file is in results
        // (to get highlights). Files outside results use "hidden:*".
        const fileEntry = search.files[fileId];
        const fileIsStale = fileEntry?.stale ?? false;
        const fileIsInResults = fileEntry?.meta != null && !fileIsStale;
        const activeQuery = fileIsStale
            ? null
            : (query ?? (fileIsInResults ? search.query : null));

        const searchQuery: SearchQuery = activeQuery
            ? { ...activeQuery, query: activeQuery.query ?? "", id: null }
            : {
                  id: null,
                  query: "hidden:*",
                  keepAlive: null,
                  sortField: null,
                  sortDirection: null,
                  sortId: null,
                  pageSize: null,
              };
        const fields = (thunkAPI.getState() as RootState).search.previewFields;
        try {
            return {
                query: searchQuery,
                preview: await getFilePreview(fileId, searchQuery, fields),
            };
        } catch (err: any) {
            return thunkAPI.rejectWithValue({
                error: err.detail ? err.detail : err.toString(),
                fileId: fileId,
            });
        }
    },
);

export const fetchFilesCountForCustomQuery = createAsyncThunk(
    "fetchFilesCountForCustomQueryThunk",
    async (
        {
            customQueryId,
        }: {
            customQueryId: string;
        },
        thunkAPI,
    ) => {
        // Resolve from state rather than taking the object: the poll loop runs
        // independently of the sidebar, so a query can be deleted between one
        // round being scheduled and this call running.
        const { search } = thunkAPI.getState() as RootState;
        const customQuery = search.customQueries.find(
            (cq) => cq.id === customQueryId,
        );
        if (!customQuery) {
            return thunkAPI.rejectWithValue({
                error: `Unknown custom query: ${customQueryId}`,
            });
        }
        try {
            const response = await getFilesCount({
                ...customQuery.query,
                id: null,
            });
            return { response, customQueryId };
        } catch (err: any) {
            return thunkAPI.rejectWithValue({
                error: err.detail ? err.detail : err.toString(),
            });
        }
    },
);

export const fetchContentTruncatedFiles = createAsyncThunk(
    "fetchContentTruncatedFilesThunk",
    async () => {
        return getFilesCount({
            id: null,
            query: QUERY_CONTENT_TRUNCATED_FILES,
            keepAlive: null,
        });
    },
);

export const fetchAttachmentsSkippedFiles = createAsyncThunk(
    "fetchAttachmentsSkippedFilesThunk",
    async () => {
        return getFilesCount({
            id: null,
            query: QUERY_ATTACHMENTS_SKIPPED_FILES,
            keepAlive: null,
        });
    },
);

export const fetchFailedFiles = createAsyncThunk(
    "fetchFailedFilesThunk",
    async () => {
        return getFilesCount({
            id: null,
            query: QUERY_FAILED_FILES,
            keepAlive: null,
        });
    },
);

export const setFileInViewState = createAsyncThunk(
    "setFileInViewStateThunk",
    async (
        {
            fileId,
            inView,
            query,
        }: {
            fileId: string;
            inView: boolean;
            query?: SearchQuery | null;
        },
        thunkAPI,
    ) => {
        const dispatch = thunkAPI.dispatch;
        if (inView) {
            subscribeChannel(fileId, dispatch);
            const { search } = thunkAPI.getState() as RootState;
            const fileEntry = search.files[fileId];
            const activeQueryStr = search.query?.query ?? null;
            const cachedQueryStr = fileEntry?.query?.query ?? null;
            const hasValidCache =
                fileEntry?.preview != null &&
                !fileEntry?.stale &&
                cachedQueryStr === activeQueryStr;
            if (!hasValidCache) {
                await dispatch(
                    fetchPreview({ fileId: fileId, query: query ?? undefined }),
                );
            }
        }
        return {
            fileId: fileId,
            inView: inView,
        };
    },
);

export const searchSlice = createSlice({
    name: "search",
    initialState,
    reducers: {
        setLeftSidebarPanel: (
            state,
            action: PayloadAction<LeftSidebarPanel | null>,
        ) => {
            state.leftSidebarPanel = action.payload;
            if (action.payload !== LeftSidebarPanel.QUERIES) {
                state.highlightedQueryId = null;
            }
        },
        setHighlightedQueryId: (
            state,
            action: PayloadAction<string | null>,
        ) => {
            state.highlightedQueryId = action.payload;
        },
        openFileTab: (
            state,
            action: PayloadAction<{
                fileId: string;
                detailTab?: FileDetailTab;
                background?: boolean;
            }>,
        ) => {
            const {
                fileId,
                detailTab = FileDetailTab.Rendered,
                background = false,
            } = action.payload;
            const existing = state.openFileTabs.find(
                (t) => t.fileId === fileId,
            );
            if (!existing) {
                state.openFileTabs.push({ fileId, detailTab });
            }
            if (!background) {
                state.activeTabFileId = fileId;
            }
        },
        closeFileTab: (state, action: PayloadAction<string>) => {
            const fileId = action.payload;
            const idx = state.openFileTabs.findIndex(
                (t) => t.fileId === fileId,
            );
            if (idx === -1) return;
            state.openFileTabs.splice(idx, 1);
            if (state.pendingFullscreenFileId === fileId) {
                state.pendingFullscreenFileId = null;
            }
            if (state.activeTabFileId === fileId) {
                if (state.openFileTabs.length === 0) {
                    state.activeTabFileId = null;
                } else {
                    state.activeTabFileId =
                        state.openFileTabs[Math.max(0, idx - 1)].fileId;
                }
            }
        },
        setActiveTabFileId: (state, action: PayloadAction<string | null>) => {
            state.activeTabFileId = action.payload;
        },
        setFileTabDetailTab: (
            state,
            action: PayloadAction<{ fileId: string; detailTab: FileDetailTab }>,
        ) => {
            const tab = state.openFileTabs.find(
                (t) => t.fileId === action.payload.fileId,
            );
            if (tab) tab.detailTab = action.payload.detailTab;
        },
        setRightSidebarTab: (state, action: PayloadAction<RightSidebarTab>) => {
            state.rightSidebarTab = action.payload;
        },
        toggleRightSidebar: (state) => {
            state.rightSidebarTab =
                state.rightSidebarTab !== null
                    ? null
                    : RightSidebarTab.STATISTICS;
        },
        closeLeftSidebar: (state) => {
            state.leftSidebarPanel = null;
        },
        closeRightSidebar: (state) => {
            state.rightSidebarTab = null;
        },
        addCustomQuery: (state, action: PayloadAction<CustomQuery>) => {
            state.customQueries.push(action.payload);
        },
        deleteCustomQuery: (state, action: PayloadAction<CustomQuery>) => {
            state.customQueries = state.customQueries.filter(
                (cq) => cq.id !== action.payload.id,
            );
        },
        markCustomQueryAsRead: (state, action: PayloadAction<CustomQuery>) => {
            const query = state.customQueries.find(
                (cq) => cq.id === action.payload.id,
            );
            if (!query) return;
            query.hasNewFiles = false;
            // Read fileCount from state, not from the payload: call sites hold
            // a render-time snapshot that a poll may already have superseded.
            query.lastSeenCount = query.fileCount;
        },
        clearStats: (state) => {
            state.stats.termsData = null;
            state.stats.histogramData = null;
        },
        fillTermsData: (
            state,
            action: PayloadAction<TermsStatisticsModel | null>,
        ) => {
            state.stats.termsData = action.payload;
        },
        fillHistogramData: (
            state,
            action: PayloadAction<GroupedHistogramStatisticsModel | null>,
        ) => {
            state.stats.histogramData = action.payload;
        },
        setTags: (state, action: PayloadAction<string[]>) => {
            state.tags = action.payload;
        },
        setWebSocketPubSubMessage: (
            state,
            action: PayloadAction<PubSubMessage>,
        ) => {
            state.webSocketPubSubMessage = action.payload;
        },
        fillTermsStats: (state, action: PayloadAction<AvailableStat[]>) => {
            state.termsStats = action.payload;
        },
        fillHistogramStats: (state, action: PayloadAction<AvailableStat[]>) => {
            state.histogramStats = action.payload;
        },
        setDisplayStat: (state, action: PayloadAction<string>) => {
            state.displayStat = action.payload;
        },
        setDisplayHistogramStat: (state, action: PayloadAction<string>) => {
            state.displayHistogramStat = action.payload;
        },
        setSummarizationSystemPrompt: (
            state,
            action: PayloadAction<string>,
        ) => {
            state.summarizationSystemPrompt = action.payload;
        },
        setVisionSystemPrompt: (state, action: PayloadAction<string>) => {
            state.visionSystemPrompt = action.payload;
        },
        setAutoActionPreference: (
            state,
            action: PayloadAction<{
                key: keyof AutoActionsPreferences;
                value: boolean;
            }>,
        ) => {
            state.autoActionsPreferences[action.payload.key] =
                action.payload.value;
        },
        setSuppressDownloadWarning: (state, action: PayloadAction<boolean>) => {
            state.suppressDownloadWarning = action.payload;
        },
        setHighlightedFileId: (state, action: PayloadAction<string | null>) => {
            state.highlightedFileId = action.payload;
        },
        bumpHighlightScroll: {
            reducer: (state, action: PayloadAction<"smart" | "top">) => {
                state.highlightScrollRequest += 1;
                state.highlightScrollMode = action.payload;
            },
            prepare: (mode: "smart" | "top" = "smart") => ({
                payload: mode,
            }),
        },
        setTemporaryFileId: (state, action: PayloadAction<string | null>) => {
            if (
                state.temporaryFileId &&
                state.temporaryFileId !== action.payload
            ) {
                delete state.files[state.temporaryFileId];
            }
            state.temporaryFileId = action.payload;
            if (action.payload && !state.files[action.payload]) {
                state.files[action.payload] = {
                    meta: null,
                    preview: null,
                    query: null,
                    temporary: true,
                };
            }
        },
        setExpandFilePaths: (state, action: PayloadAction<boolean>) => {
            state.expandFilePaths = action.payload;
        },
        // Spacing only. Which elements are shown is the other axis and is
        // left exactly as the user left it - that separation is what removed
        // the "custom" mode, which existed only to say "do not overwrite my
        // switches".
        setCardDensity: (state, action: PayloadAction<CardDensity>) => {
            state.cardDensity = action.payload;
        },
        // Both axes at once: the preset buttons are a shortcut to a whole
        // look, not a mode the card stays in. "auto" is a preset like the
        // others - it applies the look the window resolved to and leaves the
        // spacing free to follow it.
        applyDensityPreset: (state, action: PayloadAction<CardDensity>) => {
            const preset =
                action.payload === "auto"
                    ? state.autoDetectedDensity
                    : action.payload;
            state.cardDensity = action.payload;
            Object.assign(state, DENSITY_PRESETS[preset]);
        },
        setAutoDetectedDensity: (
            state,
            action: PayloadAction<NamedDensity>,
        ) => {
            const previous = state.autoDetectedDensity;
            state.autoDetectedDensity = action.payload;
            // While the switches still read exactly as some preset left them,
            // nobody has expressed a preference and auto keeps adapting them
            // to the width. The first switch the user flips ends that for
            // good: a deliberate choice is never overwritten by a resize.
            if (
                state.cardDensity === "auto" &&
                matchesPreset(state, DENSITY_PRESETS[previous])
            ) {
                Object.assign(state, DENSITY_PRESETS[action.payload]);
            }
        },
        // Deliberately does NOT force cardDensity to "custom": the density
        // preset decides which card elements are visible, while fieldLayout
        // only decides how a visible field is drawn. Coupling them would drop
        // the user out of "auto" and freeze visibility behind their back.
        setFieldLayout: (state, action: PayloadAction<FieldLayout>) => {
            state.fieldLayout = action.payload;
        },
        setPreviewFields: (state, action: PayloadAction<string[]>) => {
            state.previewFields = action.payload;
        },
        // Replaces the whole map rather than one column: a drag moves the
        // border between two columns, so it always settles two of them.
        setFieldColumnWidths: (
            state,
            action: PayloadAction<Record<string, number>>,
        ) => {
            state.fieldColumnWidths = action.payload;
        },
        // null hands the column back to the density preset.
        setThumbnailColumnWidth: (
            state,
            action: PayloadAction<number | null>,
        ) => {
            state.thumbnailColumnWidth = action.payload;
        },
        setFieldExpansion: (
            state,
            action: PayloadAction<{ field: string; expanded: boolean }>,
        ) => {
            state.fieldExpansion[action.payload.field] =
                action.payload.expanded;
        },
        setAvailablePreviewFields: (
            state,
            action: PayloadAction<PreviewField[]>,
        ) => {
            state.availablePreviewFields = action.payload;
        },
        setShowThumbnails: (state, action: PayloadAction<boolean>) => {
            state.showThumbnails = action.payload;
        },
        setShowHighlights: (state, action: PayloadAction<boolean>) => {
            state.showHighlights = action.payload;
        },
        setShowFieldSections: (state, action: PayloadAction<boolean>) => {
            state.showFieldSections = action.payload;
        },
        setShowExtensionIcon: (state, action: PayloadAction<boolean>) => {
            state.showExtensionIcon = action.payload;
        },
        setShowFilePath: (state, action: PayloadAction<boolean>) => {
            state.showFilePath = action.payload;
        },
        setShowParentNavigation: (state, action: PayloadAction<boolean>) => {
            state.showParentNavigation = action.payload;
        },
        setShowStatusIndicators: (state, action: PayloadAction<boolean>) => {
            state.showStatusIndicators = action.payload;
        },
        setShowAttachments: (state, action: PayloadAction<boolean>) => {
            state.showAttachments = action.payload;
        },
        setShowTags: (state, action: PayloadAction<boolean>) => {
            state.showTags = action.payload;
        },
        setShowActions: (state, action: PayloadAction<boolean>) => {
            state.showActions = action.payload;
        },
        setShowSortIndicator: (state, action: PayloadAction<boolean>) => {
            state.showSortIndicator = action.payload;
        },
        setShowFieldActions: (state, action: PayloadAction<boolean>) => {
            state.showFieldActions = action.payload;
        },
        setFolderViewExpandedNodes: (
            state,
            action: PayloadAction<string[]>,
        ) => {
            state.folderViewExpandedNodes = action.payload;
        },
        setFilteredFolderViewExpandedNodes: (
            state,
            action: PayloadAction<string[]>,
        ) => {
            state.filteredFolderViewExpandedNodes = action.payload;
        },
        setPendingFullscreenFileId: (
            state,
            action: PayloadAction<string | null>,
        ) => {
            state.pendingFullscreenFileId = action.payload;
        },
        toggleShowChatReasoning: (state) => {
            state.showChatReasoning = !state.showChatReasoning;
        },
        setFilePreview: (
            state,
            action: PayloadAction<GetFilePreviewResponse>,
        ) => {
            const preview = action.payload;
            if (state.files[preview.fileId]) {
                state.files[preview.fileId].preview = preview;
            }
        },
        setBinding: (
            state,
            action: PayloadAction<{ actionId: string; keys: string[] }>,
        ) => {
            state.bindings[action.payload.actionId] = [
                action.payload.keys.join(" + "),
            ];
        },
        resetBinding: (state, action: PayloadAction<string>) => {
            delete state.bindings[action.payload];
        },
        resetAllBindings: (state) => {
            state.bindings = {};
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(
                fetchFilesCountForCustomQuery.fulfilled,
                (state, action) => {
                    const customQuery = state.customQueries.find(
                        (cq) => cq.id === action.payload.customQueryId,
                    );
                    if (!customQuery) return;

                    const newFileCount = action.payload.response.totalFiles;
                    // Compare against lastSeenCount, not fileCount: fileCount
                    // tracks every poll, so comparing against it would let a
                    // drop in matches quietly raise the bar for the next badge.
                    customQuery.hasNewFiles =
                        newFileCount > customQuery.lastSeenCount ||
                        customQuery.hasNewFiles; // has new files or already had new files
                    customQuery.fileCount = newFileCount;
                },
            )
            .addCase(fetchContentTruncatedFiles.fulfilled, (state, action) => {
                state.contentTruncatedFilesCount = action.payload.totalFiles;
            })
            .addCase(
                fetchAttachmentsSkippedFiles.fulfilled,
                (state, action) => {
                    state.attachmentsSkippedFilesCount =
                        action.payload.totalFiles;
                },
            )
            .addCase(fetchFailedFiles.fulfilled, (state, action) => {
                state.failedFilesCount = action.payload.totalFiles;
            })
            .addCase(updateQuery.fulfilled, (state, action) => {
                if (!action.payload) {
                    if (state.query) state.query.query = "";
                    state.totalFiles = 0;
                    Object.keys(state.files).forEach((fileId) => {
                        state.files[fileId].meta = null;
                    });
                    if (state.temporaryFileId) {
                        delete state.files[state.temporaryFileId];
                        state.temporaryFileId = null;
                    }
                    return;
                }
                const isNewQuery = state.query?.id !== action.payload.query.id;
                // Computed before files change so we can use them after.
                const isInitialLoad = state.query === null;
                const isSameQueryString =
                    state.query?.query === action.payload.query.query;
                if (isNewQuery) {
                    // Preserve files that have open tabs so their panels stay intact,
                    // but null out meta so they don't appear in the search results card view.
                    // Stale cards are intentionally cleared here so they don't accumulate.
                    const openTabIds = new Set(
                        state.openFileTabs.map((t) => t.fileId),
                    );
                    const preserved: typeof state.files = {};
                    openTabIds.forEach((id) => {
                        if (state.files[id]) {
                            preserved[id] = {
                                ...state.files[id],
                                meta: null,
                                // The highlight does not survive a new query,
                                // so a flag carried over here would never be
                                // cleared and would append the id to the
                                // temporary tail of selectOrderedFileIds with
                                // no card for it. The keep-alive branch below
                                // restores the flag where it still applies.
                                temporary: false,
                            };
                        }
                    });
                    // For ID-only changes (keep-alive renewal, React strict-mode
                    // double-mount with the same query string), also preserve the
                    // temporary file so an out-of-results highlight is not lost.
                    if (
                        isSameQueryString &&
                        state.temporaryFileId &&
                        state.files[state.temporaryFileId]
                    ) {
                        preserved[state.temporaryFileId] =
                            state.files[state.temporaryFileId];
                    }
                    state.files = preserved;
                    state.filesInView = [];
                    // For pure ID changes (keep-alive renewal, React strict-mode
                    // double-mount) preserve the current index and temporary file unchanged.
                    // For a genuine new search query capture the highlighted file ID
                    // so it can be restored once the new results arrive below.
                    if (!isSameQueryString && !isInitialLoad) {
                        state.highlightedFileId = null;
                    }
                    if (!isSameQueryString) {
                        state.temporaryFileId = null;
                    }
                }

                state.query = action.payload.query;
                action.payload.files.forEach((file) => {
                    if (!state.files[file.fileId]) {
                        state.files[file.fileId] = {
                            meta: file,
                            preview: null,
                            query: null,
                        };
                    } else {
                        // same query, new page: preserve preview; file is back in
                        // results so clear any stale flag
                        state.files[file.fileId].meta = file;
                        state.files[file.fileId].stale = false;
                        // A hit is a result, never an out-of-results highlight.
                        // The two carriers of that state are independent and
                        // both have to go: the per-entry flag would list the id
                        // twice in selectOrderedFileIds, once as a result and
                        // once in the temporary tail, and `temporaryFileId`
                        // would render a second card for it in DetailedView.
                        state.files[file.fileId].temporary = false;
                        if (state.temporaryFileId === file.fileId) {
                            state.temporaryFileId = null;
                        }
                    }
                });
                state.totalFiles = action.payload.totalFiles;
                state.lastFileSortId =
                    action.payload.files?.at(-1)?.sortId ?? null;
                state.queryError = undefined;
            })
            .addCase(updateQuery.rejected, (state, action: any) => {
                if (action.meta.aborted) return;
                state.queryError = action.payload;
                toast.error(
                    t("error.searchResultLoadingError", {
                        error: action.payload,
                    }),
                );
            })
            .addCase(fetchPreview.fulfilled, (state, action) => {
                if (!action.payload) return;
                const { query, preview } = action.payload;
                const file = state.files[preview.fileId];
                if (file) {
                    file.preview = preview;
                    file.query = query;
                } else {
                    state.files[preview.fileId] = {
                        meta: null,
                        preview: preview,
                        query: query,
                    };
                }
            })
            .addCase(fetchPreview.rejected, (state, action) => {
                const { fileId } = action.payload as {
                    fileId: string;
                };

                // Mark as stale instead of deleting so the card stays visible
                // when a file no longer matches the current query. Clear the
                // query so fetchFileContent doesn't fire with the stale query
                // before fetchPreview returns a fresh hidden:* one.
                if (fileId && state.files[fileId]) {
                    state.files[fileId].stale = true;
                    state.files[fileId].query = null;
                }
            })
            .addCase(setFileInViewState.fulfilled, (state, action) => {
                const { fileId, inView } = action.payload;
                if (!(fileId in state.files)) return;
                if (inView) {
                    if (!state.filesInView.includes(fileId)) {
                        state.filesInView = [...state.filesInView, fileId];
                    }
                } else {
                    state.filesInView = state.filesInView.filter(
                        (i) => i !== fileId,
                    );
                }
            });
    },
});

export const {
    setLeftSidebarPanel,
    closeLeftSidebar,
    closeRightSidebar,
    setHighlightedQueryId,
    openFileTab,
    closeFileTab,
    setActiveTabFileId,
    setFileTabDetailTab,
    setRightSidebarTab,
    toggleRightSidebar,
    addCustomQuery,
    deleteCustomQuery,
    markCustomQueryAsRead,
    clearStats,
    fillTermsData,
    fillHistogramData,
    fillTermsStats,
    fillHistogramStats,
    setTags,
    setWebSocketPubSubMessage,
    setDisplayStat,
    setDisplayHistogramStat,
    setSummarizationSystemPrompt,
    setVisionSystemPrompt,
    setFilePreview,
    setHighlightedFileId,
    bumpHighlightScroll,
    setTemporaryFileId,
    setAutoActionPreference,
    setExpandFilePaths,
    setSuppressDownloadWarning,
    setFolderViewExpandedNodes,
    setFilteredFolderViewExpandedNodes,
    setPendingFullscreenFileId,
    setCardDensity,
    applyDensityPreset,
    setAutoDetectedDensity,
    setFieldLayout,

    setPreviewFields,
    setFieldColumnWidths,
    setThumbnailColumnWidth,
    setAvailablePreviewFields,
    setFieldExpansion,
    setShowThumbnails,
    setShowHighlights,
    setShowFieldSections,
    setShowExtensionIcon,
    setShowFilePath,
    setShowParentNavigation,
    setShowStatusIndicators,
    setShowAttachments,
    setShowTags,
    setShowActions,
    setShowSortIndicator,
    setShowFieldActions,
    toggleShowChatReasoning,
    setBinding,
    resetBinding,
    resetAllBindings,
} = searchSlice.actions;

export const openFileTabThunk = createAsyncThunk(
    "openFileTabThunk",
    (
        payload: {
            fileId: string;
            detailTab?: FileDetailTab;
            background?: boolean;
        },
        thunkAPI,
    ) => {
        const { fileId } = payload;
        thunkAPI.dispatch(openFileTab(payload));
        subscribeChannel(fileId, thunkAPI.dispatch);
    },
);

export const closeFileTabThunk = createAsyncThunk(
    "closeFileTabThunk",
    (fileId: string, thunkAPI) => {
        thunkAPI.dispatch(closeFileTab(fileId));
        unsubscribeChannel(fileId, thunkAPI.dispatch);
    },
);

export const selectSearch = (state: RootState) => state.search;

export const selectCustomQueries = createSelector(
    selectSearch,
    (search) => search.customQueries,
);

export const selectLeftSidebarPanel = createSelector(
    selectSearch,
    (search) => search.leftSidebarPanel,
);

export const selectHighlightedQueryId = createSelector(
    selectSearch,
    (search) => search.highlightedQueryId,
);

export const selectOpenFileTabs = createSelector(
    selectSearch,
    (search) => search.openFileTabs,
);

export const selectActiveTabFileId = createSelector(
    selectSearch,
    (search) => search.activeTabFileId,
);

export const selectRightSidebarOpen = createSelector(
    selectSearch,
    (search) => search.rightSidebarTab !== null,
);

export const selectRightSidebarTab = createSelector(
    selectSearch,
    (search) => search.rightSidebarTab,
);

export const selectAutoActionsPreferences = createSelector(
    selectSearch,
    (search) => search.autoActionsPreferences,
);

export const selectSuppressDownloadWarning = createSelector(
    selectSearch,
    (search) => search.suppressDownloadWarning,
);

export const selectQuery = createSelector(
    selectSearch,
    (search) => search.query,
);

export const selectQueryError = createSelector(
    selectSearch,
    (search) => search.queryError,
);

export const selectTags = createSelector(selectSearch, (search) => search.tags);

export const selectFiles = createSelector(
    selectSearch,
    (search) => search.files,
);
export const selectLastFileSortId = createSelector(
    selectSearch,
    (search) => search.lastFileSortId,
);

export const selectFileById = (fileId: string) =>
    createSelector([selectFiles], (files) => files[fileId]);

export const selectStatsData = createSelector(
    selectSearch,
    (search) => search.stats,
);

export const selectContentTruncatedFilesCount = createSelector(
    selectSearch,
    (search) => search.contentTruncatedFilesCount,
);

export const selectAttachmentsSkippedFilesCount = createSelector(
    selectSearch,
    (search) => search.attachmentsSkippedFilesCount,
);

export const selectFailedFilesCount = createSelector(
    selectSearch,
    (search) => search.failedFilesCount,
);

export const selectTotalFiles = createSelector(
    selectSearch,
    (search) => search.totalFiles,
);
// How many hits of the current query have been loaded, counted by `meta` so it
// stays in step with the result segment of `selectOrderedFileIds` and with the
// cards DetailedView renders. Cache entries that are not hits (open tabs,
// fetched previews, the temporary highlight) carry `meta: null` and are
// excluded; stale cards keep their `meta` and are counted, because they stay on
// screen as results. That makes this the number of hits the backend has
// reported for this query so far — not a value `totalFiles` is guaranteed to
// bound, since `totalFiles` is refetched on every page and a card can outlive
// the hit it came from.
export const selectLoadedFiles = createSelector(
    selectFiles,
    (files) => Object.values(files).filter(isLoadedResult).length,
);

export const selectFilesInView = createSelector(
    selectSearch,
    (search) => search.filesInView,
);

export const selectDisplayStat = createSelector(
    selectSearch,
    (search) => search.displayStat,
);

export const selectDisplayHistogramStat = createSelector(
    selectSearch,
    (search) => search.displayHistogramStat,
);

export const selectHistogramData = createSelector(
    selectSearch,
    (search) => search.stats.histogramData,
);

export const selectTermsStats = createSelector(
    selectSearch,
    (search) => search.termsStats,
);

export const selectHistogramStats = createSelector(
    selectSearch,
    (search) => search.histogramStats,
);

export const selectWebSocketPubSubMessage = createSelector(
    selectSearch,
    (search) => search.webSocketPubSubMessage,
);

export const selectSummarizationSystemPrompt = createSelector(
    selectSearch,
    (search) => search.summarizationSystemPrompt,
);

export const selectVisionSystemPrompt = createSelector(
    selectSearch,
    (search) => search.visionSystemPrompt,
);

export const selectTemporaryFileId = createSelector(
    selectSearch,
    (search) => search.temporaryFileId,
);

export const selectExpandFilePaths = createSelector(
    selectSearch,
    (search) => search.expandFilePaths,
);

// Memoised list of ordered file IDs matching the order used in DetailedView.
// Extracted as a standalone selector so it is not recomputed on every keypress
// when only the highlighted index changes.
export const selectOrderedFileIds = createSelector(selectFiles, (files) => [
    ...Object.keys(files).filter((id) => isLoadedResult(files[id])),
    ...Object.keys(files).filter((id) => files[id].temporary),
]);

export const selectHighlightedFileId = createSelector(
    selectSearch,
    (search) => search.highlightedFileId,
);

export const selectHighlightScrollRequest = createSelector(
    selectSearch,
    (search) => search.highlightScrollRequest,
);

export const selectHighlightScrollMode = createSelector(
    selectSearch,
    (search) => search.highlightScrollMode,
);

export const selectPendingFullscreenFileId = createSelector(
    selectSearch,
    (search) => search.pendingFullscreenFileId,
);

export const selectFolderViewExpandedNodes = createSelector(
    selectSearch,
    (search) => search.folderViewExpandedNodes,
);

export const selectFilteredFolderViewExpandedNodes = createSelector(
    selectSearch,
    (search) => search.filteredFolderViewExpandedNodes,
);

export const selectCardDensity = createSelector(
    selectSearch,
    (search) => search.cardDensity,
);

export const selectResolvedCardDensity = createSelector(
    selectSearch,
    (search): NamedDensity =>
        search.cardDensity === "auto"
            ? search.autoDetectedDensity
            : search.cardDensity,
);

export const selectFieldLayout = createSelector(
    selectSearch,
    (search) => search.fieldLayout,
);

/**
 * Whether the result list draws its rows gapless, with a hairline and
 * alternating backgrounds instead of a gap between cards.
 *
 * Single owner of that decision: the list sets the chrome and each card marks
 * its cursor to match, and the two must agree - a halo needs the gap the flat
 * list does not have.
 *
 * Read from the spacing alone. The field layout decides how a field is drawn
 * and nothing else: a renderer that also rewrote the list's chrome is why
 * neither control could be trusted to say what the cards would look like.
 */
export const selectFlatRowChrome = createSelector(
    selectResolvedCardDensity,
    (density) => density === "compact",
);

export const selectFieldExpansion = createSelector(
    selectSearch,
    (search) => search.fieldExpansion,
);

export const selectPreviewFields = createSelector(
    selectSearch,
    (search) => search.previewFields,
);

export const selectFieldColumnWidths = createSelector(
    selectSearch,
    (search) => search.fieldColumnWidths,
);

export const selectThumbnailColumnWidth = createSelector(
    selectSearch,
    (search) => search.thumbnailColumnWidth,
);

export const selectAvailablePreviewFields = createSelector(
    selectSearch,
    (search) => search.availablePreviewFields,
);

export const selectShowThumbnails = createSelector(
    selectSearch,
    (search) => search.showThumbnails,
);

export const selectShowHighlights = createSelector(
    selectSearch,
    (search) => search.showHighlights,
);

export const selectCardElementVisibility = createSelector(
    selectSearch,
    (search): CardVisibilitySettings => ({
        showThumbnails: search.showThumbnails,
        showHighlights: search.showHighlights,
        showFieldSections: search.showFieldSections,
        showExtensionIcon: search.showExtensionIcon,
        showFilePath: search.showFilePath,
        showParentNavigation: search.showParentNavigation,
        showStatusIndicators: search.showStatusIndicators,
        showAttachments: search.showAttachments,
        showTags: search.showTags,
        showActions: search.showActions,
        showSortIndicator: search.showSortIndicator,
        showFieldActions: search.showFieldActions,
    }),
);

/**
 * The preset the card currently reads as, or null once the switches have been
 * taken somewhere no preset describes.
 *
 * Derived rather than stored: a "custom" flag is this same observation kept
 * as state, and state that restates what is already knowable is state that
 * can disagree with it.
 */
export const selectMatchingDensityPreset = createSelector(
    selectCardElementVisibility,
    selectResolvedCardDensity,
    (visibility, density): NamedDensity | null =>
        matchesPreset(visibility, DENSITY_PRESETS[density]) ? density : null,
);

export const selectShowChatReasoning = createSelector(
    selectSearch,
    (search) => search.showChatReasoning,
);

export const selectShortcutsBindings = createSelector(
    selectSearch,
    (search) => search.bindings,
);

export const selectResolvedBindings = createSelector(
    [selectShortcutsBindings],
    (bindings) => {
        const resolved: Record<string, string[]> = {};
        for (const action of shortcutRegistry) {
            resolved[action.id] =
                bindings[action.id] !== undefined
                    ? bindings[action.id]
                    : action.defaultKeys;
        }
        return resolved;
    },
);

export const selectReverseBindings = createSelector(
    selectResolvedBindings,
    (resolvedBindings) => {
        const reverse: Record<string, string> = {};
        for (const [actionId, keys] of Object.entries(resolvedBindings)) {
            for (const key of keys) {
                // Normalize the key for case-insensitive matching
                const normalizedKey = key
                    .split(" + ")
                    .map((part) => part.trim().toLowerCase())
                    .join(" + ");
                reverse[normalizedKey] = actionId;
            }
        }
        return reverse;
    },
);

export default searchSlice.reducer;
