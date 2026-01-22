import {
    createAsyncThunk,
    createSelector,
    createSlice,
    PayloadAction,
} from "@reduxjs/toolkit";
import { RootState } from "../../app/store";
import { toast } from "react-toastify";
import {
    startLoadingIndicator,
    stopLoadingIndicator,
} from "../common/commonSlice.ts";
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
} from "../../app/api";
import {
    CombinedStats,
    FileDetailData as FileDetailData,
    SearchQuery,
    SearchQuerySchema,
} from "./model.ts";
import { webSocketSendMessage } from "../../middleware/SocketMiddleware.ts";

import { v4 as uuidv4 } from "uuid";
import { t } from "i18next";
import Ajv, { JSONSchemaType } from "ajv";

export enum SearchView {
    FOLDER = "folder",
    DETAILED = "detailed",
    STATISTICS = "statistics",
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

export function initCustomQuery(
    query: SearchQuery,
    fileCount: number,
    name: string,
    icon: string,
): CustomQuery {
    return {
        id: uuidv4(),
        query,
        fileCount,
        hasNewFiles: false,
        name,
        icon,
    } as CustomQuery;
}

export interface SearchState {
    query: SearchQuery | null;
    queryError?: string;
    view: SearchView;
    stats: CombinedStats;
    files: {
        [fileId: string]: {
            meta: GetFilesFileEntry;
            preview: GetFilePreviewResponse | null;
        };
    };
    fileDetailData: FileDetailData | null;
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
}

export const CUSTOM_QUERIES_LOCAL_STORAGE_KEY = "CUSTOM_QUERIES";
export const QUERY_FAILED_FILES = "state:failed";
export const QUERY_CONTENT_TRUNCATED_FILES = "content_truncated:true";
const AJV = new Ajv();

function loadCustomQueries(): CustomQuery[] {
    const data = window.localStorage.getItem(CUSTOM_QUERIES_LOCAL_STORAGE_KEY);
    if (data === null) return [];

    try {
        const parsed = JSON.parse(data);
        if (!Array.isArray(parsed)) {
            console.warn("Invalid custom queries data format");
            return [];
        }

        const validate = AJV.compile(CustomQuerySchema);
        const validQueries: CustomQuery[] = [];

        for (const query of parsed) {
            if (validate(query)) {
                validQueries.push(query);
            } else {
                console.warn(
                    `Invalid custom query "${query?.name || "Unknown"}" was removed`,
                );
            }
        }

        return validQueries;
    } catch {
        console.warn("Failed to load custom queries");
        return [];
    }
}

const initialState: SearchState = {
    query: null,
    view: SearchView.DETAILED,
    stats: {
        summary: null,
        generic: null,
        tags: null,
    },
    files: {},
    fileDetailData: null,
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
};

export const updateQuery = createAsyncThunk(
    "updateQueryThunk",
    async (query: Partial<SearchQuery>, thunkAPI) => {
        const dispatch = thunkAPI.dispatch;
        const lastQuery = (thunkAPI.getState() as RootState).search.query;
        const queryId = query.id ?? (await getLongRunningQuery()).queryId;
        const queryQuery = query.query ?? lastQuery?.query ?? "";

        if (queryQuery.trim().length === 0) {
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
            const searchResult = searchFiles(newQuery);
            const countResult = getFilesCount(newQuery);
            const result = {
                ...(await searchResult),
                ...(await countResult),
                query: newQuery,
            };

            if (queryIdChanged && lastQuery?.id != null) {
                dispatch(
                    webSocketSendMessage({
                        message: {
                            type: "unsubscribe",
                            channels: [lastQuery.id],
                        },
                    }),
                );
            }
            return result;
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
            let errorDetail = "";
            if (error instanceof ResponseError) {
                const errorData = await error.response.json();
                errorDetail = errorData?.detail ?? JSON.stringify(errorData);
            } else {
                errorDetail = error.toString();
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
        }: {
            fileId: string;
        },
        thunkAPI,
    ) => {
        const searchState = (thunkAPI.getState() as RootState).search;
        const file = searchState.files[fileId];
        if (!file || searchState.query == null) return;
        const query = {
            ...searchState.query,
            // update query id
            id: (await getShortRunningQuery()).queryId,
            query: searchState.query?.query ?? "",
        } satisfies SearchQuery;
        try {
            return await getFilePreview(fileId, query);
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
            return {
                response: await getFilesCount({
                    ...customQuery.query,
                    id: (await getShortRunningQuery()).queryId,
                }),
                customQueryId: customQuery.id,
            };
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
            const customQuery: CustomQuery = action.payload;
            state.customQueries.push(customQuery);
        },
        deleteCustomQuery: (state, action: PayloadAction<CustomQuery>) => {
            const toRemove = state.customQueries.find(
                (cq) => cq.id == action.payload.id,
            );

            if (toRemove) {
                const index = state.customQueries.indexOf(toRemove);
                state.customQueries.splice(index, 1);
            }
        },
        markCustomQueryAsRead: (state, action: PayloadAction<CustomQuery>) => {
            const toMark = state.customQueries.find(
                (cq) => cq.id == action.payload.id,
            );

            if (toMark) {
                toMark.hasNewFiles = false;
            }
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
        setFileDetailData: (
            state,
            action: PayloadAction<FileDetailData | null>,
        ) => {
            state.fileDetailData = action.payload;
        },
    },
    extraReducers: (builder) => {
        builder.addCase(
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
        );
        builder.addCase(
            fetchContentTruncatedFiles.fulfilled,
            (state, action) => {
                state.contentTruncatedFilesCount = action.payload.totalFiles;
            },
        );
        builder.addCase(fetchFailedFiles.fulfilled, (state, action) => {
            state.failedFilesCount = action.payload.totalFiles;
        });
        builder.addCase(updateQuery.fulfilled, (state, action) => {
            if (state.query?.id != action.payload?.query.id) {
                // new query: reset files
                state.files = {};
            }
            if (action.payload == null) {
                if (state.query != null) {
                    state.query.query = "";
                }
                return;
            }
            state.query = action.payload.query;

            action.payload.files.forEach((file) => {
                // initialize file in files list
                state.files[file.fileId] = {
                    meta: file,
                    preview: null,
                };
            });
            state.totalFiles = action.payload.totalFiles;
            state.lastFileSortId = action.payload.files?.at(-1)?.sortId ?? null;
            state.queryError = undefined;
        });
        builder.addCase(updateQuery.rejected, (state, action: any) => {
            const error = action.payload;
            toast.error(t("error.searchResultLoadingError", { error: error }));
            state.queryError = error;
        });
        builder.addCase(fetchPreview.fulfilled, (state, action) => {
            if (!action.payload) return;
            const preview = action.payload;
            const fileId = preview.fileId;
            const file = state.files[fileId];
            if (!file) return;
            file.preview = preview;
        });
        builder.addCase(fetchPreview.rejected, (state, action) => {
            const { fileId, error } = action.payload as {
                fileId: string;
                error: string;
            };

            if (fileId && state.files[fileId]) {
                delete state.files[fileId];
            }

            toast.error("Cannot load file preview. Error: " + error);
        });
        builder.addCase(setFileInViewState.fulfilled, (state, action) => {
            const { fileId, inView } = action.payload;
            if (fileId in state.files === false) return;
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
    setFileDetailData,
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

export const selectFileDetailData = createSelector(
    selectSearch,
    (search) => search.fileDetailData,
);

export default searchSlice.reducer;
