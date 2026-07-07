import {
    AsyncThunkConfig,
    createAsyncThunk,
    createSelector,
    createSlice,
    GetThunkAPI,
    PayloadAction,
} from "@reduxjs/toolkit";
import Ajv, { JSONSchemaType } from "ajv";
import { t } from "i18next";
import { toast } from "react-toastify";
import { v4 as uuidv4 } from "uuid";

import {
    getFilePreview,
    GetFilePreviewResponse,
    GetFilesFileEntry,
    searchFiles,
    GroupedHistogramStatisticsModel,
    TermsStatisticsModel,
    AvailableStat,
    PubSubMessage,
    getLongRunningQuery,
    getFilesCount,
    getShortRunningQuery,
    ResponseError,
} from "@app/api/index";
import {
    subscribeChannel,
    unsubscribeChannel,
} from "@app/channelSubscriptions";
import {
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import { FileDetailTab } from "@features/common/utils/enums";
import {
    CombinedStats,
    SearchQuery,
    SearchQuerySchema,
} from "@features/common/utils/model";
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
    BULK_ACTIONS: "bulk_actions",
    AUTO_ACTIONS: "auto_actions",
} as const;

export type LeftSidebarPanel =
    (typeof LeftSidebarPanel)[keyof typeof LeftSidebarPanel];

export const RightSidebarTab = {
    STATISTICS: "statistics",
    CHAT: "chat",
} as const;

export type RightSidebarTab =
    (typeof RightSidebarTab)[keyof typeof RightSidebarTab];

export interface FileTabState {
    fileId: string;
    detailTab: FileDetailTab;
}

export interface CustomQuery {
    id: string;
    query: SearchQuery;
    fileCount: number;
    hasNewFiles: boolean;
    name: string;
    icon: string;
}

const CustomQuerySchema: JSONSchemaType<CustomQuery> = {
    type: "object",
    properties: {
        id: { type: "string" },
        query: SearchQuerySchema as any,
        fileCount: { type: "number" },
        hasNewFiles: { type: "boolean" },
        name: { type: "string" },
        icon: { type: "string" },
    },
    required: ["id", "query", "fileCount", "hasNewFiles", "name", "icon"],
    additionalProperties: false,
};

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
        hasNewFiles: false,
        name,
        icon,
    };
};

export interface KeyboardNavigationState {
    highlightedIndex: number | null;
}

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
    rightSidebarOpen: boolean;
    rightSidebarTab: RightSidebarTab;
    stats: CombinedStats;
    files: {
        [fileId: string]: {
            meta: GetFilesFileEntry | null;
            preview: GetFilePreviewResponse | null;
            query: SearchQuery | null;
            stale?: boolean;
            temporary?: boolean;
        };
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
    keyboardNavigation: KeyboardNavigationState;
}

export const CUSTOM_QUERIES_LOCAL_STORAGE_KEY = "CUSTOM_QUERIES";
export const AUTO_ACTIONS_PREFERENCES_LOCAL_STORAGE_KEY =
    "AUTO_ACTIONS_PREFERENCES";
export const UI_STATE_LOCAL_STORAGE_KEY = "UI_STATE";
export const QUERY_FAILED_FILES = "state:failed";
export const QUERY_CONTENT_TRUNCATED_FILES = "content_truncated:true";
export const QUERY_ATTACHMENTS_SKIPPED_FILES = "attachments_skipped:true";
const AJV = new Ajv();

interface UiState {
    leftSidebarPanel: LeftSidebarPanel | null;
    rightSidebarOpen: boolean;
    rightSidebarTab: RightSidebarTab;
    openFileTabs: FileTabState[];
    expandFilePaths: boolean;
}

const DEFAULT_UI_STATE: UiState = {
    leftSidebarPanel: null,
    rightSidebarOpen: false,
    rightSidebarTab: RightSidebarTab.STATISTICS,
    openFileTabs: [],
    expandFilePaths: false,
};

const UiStateSchema = {
    type: "object",
    properties: {
        leftSidebarPanel: {
            type: ["string", "null"],
            enum: [...Object.values(LeftSidebarPanel), null],
        },
        rightSidebarOpen: { type: "boolean" },
        rightSidebarTab: {
            type: "string",
            enum: Object.values(RightSidebarTab),
        },
        openFileTabs: {
            type: "array",
            items: {
                type: "object",
                properties: {
                    fileId: { type: "string", minLength: 1 },
                    detailTab: {
                        type: "integer",
                        enum: Object.values(FileDetailTab),
                    },
                },
                required: ["fileId", "detailTab"],
                additionalProperties: false,
            },
        },
        expandFilePaths: { type: "boolean" },
    },
    required: [
        "leftSidebarPanel",
        "rightSidebarOpen",
        "rightSidebarTab",
        "openFileTabs",
        "expandFilePaths",
    ],
    additionalProperties: false,
} as const;

const loadUiState = (): UiState => {
    const data = window.localStorage.getItem(UI_STATE_LOCAL_STORAGE_KEY);
    if (!data) return DEFAULT_UI_STATE;
    try {
        const parsed = JSON.parse(data);
        const validate = AJV.compile(UiStateSchema);
        if (validate(parsed)) return parsed as UiState;
        console.warn("Invalid UI state in localStorage, using defaults");
        return DEFAULT_UI_STATE;
    } catch {
        return DEFAULT_UI_STATE;
    }
};

const DEFAULT_AUTO_ACTIONS_PREFERENCES: AutoActionsPreferences = {
    markAsSeen: true,
    flag: false,
    reindex: false,
    translate: false,
    summarize: false,
    describeImage: false,
};

const AutoActionsPreferencesSchema: JSONSchemaType<AutoActionsPreferences> = {
    type: "object",
    properties: {
        markAsSeen: { type: "boolean" },
        flag: { type: "boolean" },
        reindex: { type: "boolean" },
        translate: { type: "boolean" },
        summarize: { type: "boolean" },
        describeImage: { type: "boolean" },
    },
    required: [
        "markAsSeen",
        "flag",
        "reindex",
        "translate",
        "summarize",
        "describeImage",
    ],
    additionalProperties: false,
};

const loadAutoActionsPreferences = (): AutoActionsPreferences => {
    const data = window.localStorage.getItem(
        AUTO_ACTIONS_PREFERENCES_LOCAL_STORAGE_KEY,
    );
    if (!data) return DEFAULT_AUTO_ACTIONS_PREFERENCES;
    try {
        const parsed = JSON.parse(data);
        const validate = AJV.compile(AutoActionsPreferencesSchema);
        if (validate(parsed)) return parsed;
        console.warn(
            "Invalid auto-actions preferences in localStorage, using defaults",
        );
        return DEFAULT_AUTO_ACTIONS_PREFERENCES;
    } catch {
        return DEFAULT_AUTO_ACTIONS_PREFERENCES;
    }
};

const loadCustomQueries = (): CustomQuery[] => {
    const data = window.localStorage.getItem(CUSTOM_QUERIES_LOCAL_STORAGE_KEY);
    if (!data) return [];

    try {
        const parsed = JSON.parse(data);
        if (!Array.isArray(parsed)) {
            console.warn("Invalid custom queries data format");
            return [];
        }

        const validate = AJV.compile(CustomQuerySchema);
        return parsed.filter((q) => {
            if (validate(q)) return true;
            console.warn(
                `Invalid custom query "${q?.name || "Unknown"}" removed`,
            );
            return false;
        });
    } catch {
        console.warn("Failed to load custom queries");
        return [];
    }
};

const uiState = loadUiState();
// Seed activeTabFileId from the URL hash so the Redux→URL effect sees a match
// on initial mount and doesn't clear the hash before the URL→Redux effect can
// open the tab. The URL→Redux effect (syncedHashRef = "") still fires and calls
// openFileTabThunk to ensure the tab is added to openFileTabs if it isn't yet.
const initialHashFileId = window.location.hash.substring(1) || null;

const initialState: SearchState = {
    query: null,
    leftSidebarPanel: uiState.leftSidebarPanel,
    rightSidebarOpen: uiState.rightSidebarOpen,
    rightSidebarTab: uiState.rightSidebarTab,
    stats: {
        termsData: null,
        histogramData: null,
    },
    files: {},
    lastFileSortId: null,
    totalFiles: 0,
    filesInView: [],
    tags: [],
    customQueries: loadCustomQueries(),
    highlightedQueryId: null,
    openFileTabs: uiState.openFileTabs,
    activeTabFileId: initialHashFileId,
    expandFilePaths: uiState.expandFilePaths,
    autoActionsPreferences: loadAutoActionsPreferences(),
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
    keyboardNavigation: {
        highlightedIndex: null,
    },
    temporaryFileId: null,
};

export const updateQuery = createAsyncThunk(
    "updateQueryThunk",
    async (query: Partial<SearchQuery>, thunkAPI) => {
        const dispatch = thunkAPI.dispatch;
        const { search } = thunkAPI.getState() as RootState;
        const lastQuery = search.query;

        const queryId = query.id ?? (await getLongRunningQuery()).queryId;
        const queryQuery = query.query ?? lastQuery?.query ?? "";

        if (!queryQuery.trim()) {
            return;
        }

        const newQuery: SearchQuery = {
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

        dispatch(startLoadingIndicator());

        if (queryIdChanged) {
            dispatch(
                webSocketSendMessage({
                    message: {
                        type: "subscribe",
                        channels: [queryId],
                    },
                }),
            );
        }
        try {
            const [searchRes, countRes] = await Promise.all([
                searchFiles(newQuery),
                getFilesCount(newQuery),
            ]);

            if (queryIdChanged && lastQuery?.id) {
                dispatch(
                    webSocketSendMessage({
                        message: {
                            type: "unsubscribe",
                            channels: [lastQuery.id],
                        },
                    }),
                );
            }

            return { ...searchRes, ...countRes, query: newQuery };
        } catch (error: any) {
            if (queryIdChanged) {
                dispatch(
                    webSocketSendMessage({
                        message: {
                            type: "unsubscribe",
                            channels: [queryId],
                        },
                    }),
                );
            }
            // Get error detail
            let errorDetail = error.toString();
            if (error instanceof ResponseError) {
                const errorData = await error.response.json();
                errorDetail = errorData?.detail ?? JSON.stringify(errorData);
            }
            return thunkAPI.rejectWithValue(errorDetail);
        } finally {
            dispatch(stopLoadingIndicator());
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

        const queryId = (await getShortRunningQuery()).queryId;
        const searchQuery: SearchQuery = activeQuery
            ? { ...activeQuery, query: activeQuery.query ?? "", id: queryId }
            : {
                  id: queryId,
                  query: "hidden:*",
                  keepAlive: null,
                  sortField: null,
                  sortDirection: null,
                  sortId: null,
                  pageSize: null,
              };
        try {
            return {
                query: searchQuery,
                preview: await getFilePreview(fileId, searchQuery),
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
            customQuery,
        }: {
            customQuery: CustomQuery;
        },
        thunkAPI,
    ) => {
        try {
            const queryId = (await getShortRunningQuery()).queryId;
            const response = await getFilesCount({
                ...customQuery.query,
                id: queryId,
            });
            return { response, customQueryId: customQuery.id };
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
            id: (await getShortRunningQuery()).queryId,
            query: QUERY_CONTENT_TRUNCATED_FILES,
            keepAlive: null,
        });
    },
);

export const fetchAttachmentsSkippedFiles = createAsyncThunk(
    "fetchAttachmentsSkippedFilesThunk",
    async () => {
        return getFilesCount({
            id: (await getShortRunningQuery()).queryId,
            query: QUERY_ATTACHMENTS_SKIPPED_FILES,
            keepAlive: null,
        });
    },
);

export const fetchFailedFiles = createAsyncThunk(
    "fetchFailedFilesThunk",
    async () => {
        return getFilesCount({
            id: (await getShortRunningQuery()).queryId,
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
            await dispatch(
                fetchPreview({ fileId: fileId, query: query ?? undefined }),
            );
        } else {
            unsubscribeChannel(fileId, dispatch);
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
            state.rightSidebarOpen = true;
        },
        toggleRightSidebar: (state) => {
            state.rightSidebarOpen = !state.rightSidebarOpen;
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
            if (query) query.hasNewFiles = false;
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
        setHighlightedIndex: (state, action: PayloadAction<number | null>) => {
            if (state.temporaryFileId) {
                // Temp file is always at the index after all files that have meta
                // (matching DetailedView's allFileIds order, which includes stale).
                const metaCount = Object.keys(state.files).filter(
                    (id) => state.files[id].meta !== null,
                ).length;
                if (action.payload !== metaCount) {
                    delete state.files[state.temporaryFileId];
                    state.temporaryFileId = null;
                }
            }
            state.keyboardNavigation.highlightedIndex = action.payload;
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
        setFilePreview: (
            state,
            action: PayloadAction<GetFilePreviewResponse>,
        ) => {
            const preview = action.payload;
            if (state.files[preview.fileId]) {
                state.files[preview.fileId].preview = preview;
            }
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
                    customQuery.hasNewFiles =
                        newFileCount > customQuery.fileCount ||
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
                    return;
                }
                const isNewQuery = state.query?.id !== action.payload.query.id;
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
                            };
                        }
                    });
                    state.files = preserved;
                    state.keyboardNavigation = {
                        highlightedIndex: null,
                    };
                    state.temporaryFileId = null;
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
                    }
                });
                state.totalFiles = action.payload.totalFiles;
                state.lastFileSortId =
                    action.payload.files?.at(-1)?.sortId ?? null;
                state.queryError = undefined;
            })
            .addCase(updateQuery.rejected, (state, action: any) => {
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
    setHighlightedIndex,
    setTemporaryFileId,
    setAutoActionPreference,
    setExpandFilePaths,
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
    (search) => search.rightSidebarOpen,
);

export const selectRightSidebarTab = createSelector(
    selectSearch,
    (search) => search.rightSidebarTab,
);

export const selectAutoActionsPreferences = createSelector(
    selectSearch,
    (search) => search.autoActionsPreferences,
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
export const selectLoadedFiles = createSelector(
    selectSearch,
    (search) =>
        Object.values(search.files).filter((f) => !f.stale && !f.temporary)
            .length,
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

export const selectHighlightedIndex = createSelector(
    selectSearch,
    (search) => search.keyboardNavigation.highlightedIndex,
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
    ...Object.keys(files).filter((id) => files[id].meta !== null),
    ...Object.keys(files).filter((id) => files[id].temporary),
]);

export const selectHighlightedFileId = createSelector(
    selectOrderedFileIds,
    selectHighlightedIndex,
    (fileIds, index) => {
        if (index === null || index === undefined) return null;
        return fileIds[index] ?? null;
    },
);

export default searchSlice.reducer;
