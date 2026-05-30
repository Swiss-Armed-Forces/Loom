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
    LibretranslateSupportedLanguages,
    searchFiles,
    SummaryStatisticsModel,
    GenericStatisticsModel,
    Stat,
    PubSubMessage,
    getLongRunningQuery,
    getFilesCount,
    getShortRunningQuery,
    ResponseError,
} from "@app/api/index";
import {
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import {
    CombinedStats,
    SearchQuery,
    SearchQuerySchema,
} from "@features/common/utils/model";
import { webSocketSendMessage } from "@middleware/SocketMiddleware";

import { RootState } from "../store";

export const SearchView = {
    FOLDER: "folder",
    DETAILED: "detailed",
    STATISTICS: "statistics",
} as const;

export type SearchView = (typeof SearchView)[keyof typeof SearchView];

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

export interface SearchState {
    query: SearchQuery | null;
    queryError?: string;
    view: SearchView;
    stats: CombinedStats;
    files: {
        [fileId: string]: {
            meta: GetFilesFileEntry | null;
            preview: GetFilePreviewResponse | null;
            query: SearchQuery | null;
        };
    };
    totalFiles: number;
    lastFileSortId: any[] | null;
    filesInView: string[];
    tags: string[];
    languages: LibretranslateSupportedLanguages[] | null;
    translationLanguage: LibretranslateSupportedLanguages | null;
    customQueries: CustomQuery[];
    contentTruncatedFilesCount: number;
    failedFilesCount: number;
    displayStat: Stat;
    webSocketPubSubMessage: PubSubMessage | null;
    chatbotOpen: boolean;
    summarizationSystemPrompt: string | null;
    keyboardNavigation: KeyboardNavigationState;
}

export const CUSTOM_QUERIES_LOCAL_STORAGE_KEY = "CUSTOM_QUERIES";
export const QUERY_FAILED_FILES = "state:failed";
export const QUERY_CONTENT_TRUNCATED_FILES = "content_truncated:true";
const AJV = new Ajv();

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

const initialState: SearchState = {
    query: null,
    view: SearchView.DETAILED,
    stats: {
        summary: null,
        generic: null,
        tags: null,
    },
    files: {},
    lastFileSortId: null,
    totalFiles: 0,
    filesInView: [],
    tags: [],
    languages: null,
    translationLanguage: null,
    customQueries: loadCustomQueries(),
    contentTruncatedFilesCount: 0,
    failedFilesCount: 0,
    displayStat: Stat.Extensions,
    webSocketPubSubMessage: null,
    chatbotOpen: false,
    summarizationSystemPrompt: null,
    keyboardNavigation: {
        highlightedIndex: null,
    },
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
            languages:
                query.languages?.length === 0
                    ? null
                    : (query.languages ?? lastQuery?.languages ?? null),
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
        const queryId = (await getShortRunningQuery()).queryId;

        const searchQuery: SearchQuery = query
            ? {
                  ...query,
                  query: query.query ?? "",
                  id: queryId,
              }
            : {
                  id: queryId,
                  query: "hidden:*",
                  keepAlive: null,
                  languages: null,
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
        }: {
            fileId: string;
            inView: boolean;
        },
        thunkAPI,
    ) => {
        const dispatch = thunkAPI.dispatch;
        if (inView) {
            await Promise.all([
                dispatch(fetchPreview({ fileId: fileId })),
                dispatch(
                    webSocketSendMessage({
                        message: {
                            type: "subscribe",
                            channels: [fileId],
                        },
                    }),
                ),
            ]);
        } else {
            dispatch(
                webSocketSendMessage({
                    message: {
                        type: "unsubscribe",
                        channels: [fileId],
                    },
                }),
            );
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
        setSearchView: (state, action: PayloadAction<SearchView>) => {
            state.view = action.payload;
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
        fillStatsSummary: (
            state,
            action: PayloadAction<SummaryStatisticsModel | null>,
        ) => {
            state.stats.summary = action.payload;
        },
        fillStatsTags: (
            state,
            action: PayloadAction<GenericStatisticsModel | null>,
        ) => {
            state.stats.tags = action.payload;
        },
        fillStatsGeneric: (
            state,
            action: PayloadAction<GenericStatisticsModel | null>,
        ) => {
            state.stats.generic = action.payload;
        },
        setTags: (state, action: PayloadAction<string[]>) => {
            state.tags = action.payload;
        },
        setLanguages: (
            state,
            action: PayloadAction<LibretranslateSupportedLanguages[]>,
        ) => {
            state.languages = action.payload;
        },
        setTranslationLanguage: (
            state,
            action: PayloadAction<LibretranslateSupportedLanguages | null>,
        ) => {
            state.translationLanguage = action.payload;
        },
        setWebSocketPubSubMessage: (
            state,
            action: PayloadAction<PubSubMessage>,
        ) => {
            state.webSocketPubSubMessage = action.payload;
        },
        setDisplayStat: (state, action: PayloadAction<Stat>) => {
            state.displayStat = action.payload;
        },
        setChatbotOpen: (state, action: PayloadAction<boolean>) => {
            state.chatbotOpen = action.payload;
        },
        setSummarizationSystemPrompt: (
            state,
            action: PayloadAction<string>,
        ) => {
            state.summarizationSystemPrompt = action.payload;
        },
        setHighlightedIndex: (state, action: PayloadAction<number | null>) => {
            state.keyboardNavigation.highlightedIndex = action.payload;
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
            .addCase(fetchFailedFiles.fulfilled, (state, action) => {
                state.failedFilesCount = action.payload.totalFiles;
            })
            .addCase(updateQuery.fulfilled, (state, action) => {
                if (!action.payload) {
                    if (state.query) state.query.query = "";
                    return;
                }
                const isNewQuery = state.query?.id !== action.payload.query.id;
                if (isNewQuery) {
                    // new query: reset files and keyboard navigation
                    Object.keys(state.files).forEach((fileId) => {
                        state.files[fileId].meta = null;
                    });
                    state.keyboardNavigation = {
                        highlightedIndex: null,
                    };
                }

                state.query = action.payload.query;
                action.payload.files.forEach((file) => {
                    // Check if file already exists to preserve preview if this is just a page load/refresh
                    if (!state.files[file.fileId]) {
                        state.files[file.fileId] = {
                            meta: file,
                            preview: null,
                            query: null,
                        };
                    } else {
                        state.files[file.fileId].meta = file;
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

                if (fileId && state.files[fileId]) {
                    delete state.files[fileId];
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
    setSearchView,
    addCustomQuery,
    deleteCustomQuery,
    markCustomQueryAsRead,
    fillStatsSummary,
    fillStatsTags,
    fillStatsGeneric,
    setTags,
    setLanguages,
    setTranslationLanguage,
    setWebSocketPubSubMessage,
    setDisplayStat,
    setChatbotOpen,
    setSummarizationSystemPrompt,
    setFilePreview,
    setHighlightedIndex,
} = searchSlice.actions;

export const selectSearch = (state: RootState) => state.search;

export const selectCustomQueries = createSelector(
    selectSearch,
    (search) => search.customQueries,
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

export const selectTranslationLanguage = createSelector(
    selectSearch,
    (search) => search.translationLanguage,
);
export const selectLanguages = createSelector(
    selectSearch,
    (search) => search.languages,
);
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

export const selectFailedFilesCount = createSelector(
    selectSearch,
    (search) => search.failedFilesCount,
);
export const selectActiveSearchView = createSelector(
    selectSearch,
    (search) => search.view,
);
export const selectTotalFiles = createSelector(
    selectSearch,
    (search) => search.totalFiles,
);
export const selectLoadedFiles = createSelector(
    selectSearch,
    (search) => Object.keys(search.files).length,
);

export const selectFilesInView = createSelector(
    selectSearch,
    (search) => search.filesInView,
);

export const selectDisplayStat = createSelector(
    selectSearch,
    (search) => search.displayStat,
);

export const selectWebSocketPubSubMessage = createSelector(
    selectSearch,
    (search) => search.webSocketPubSubMessage,
);

export const selectSummarizationSystemPrompt = createSelector(
    selectSearch,
    (search) => search.summarizationSystemPrompt,
);

export const selectHighlightedIndex = createSelector(
    selectSearch,
    (search) => search.keyboardNavigation.highlightedIndex,
);

export default searchSlice.reducer;
