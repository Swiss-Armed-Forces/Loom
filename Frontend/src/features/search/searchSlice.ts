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
    GetFilesResponse,
    LibretranslateSupportedLanguages,
    searchFiles,
    SummaryStatisticsModel,
    GenericStatisticsModel,
    Stat,
    PubSubMessage,
    SortId,
} from "../../app/api";
import { CombinedStats, SearchQuery } from "./model.ts";
import { webSocketSendMessage } from "../../middleware/SocketMiddleware.ts";
import { defaultPageSize } from "./SearchQueryUtils.ts";

import { v4 as uuidv4 } from "uuid";

export enum SearchView {
    FOLDER = "folder",
    DETAILED = "detailed",
    STATISTICS = "statistics",
}

export interface CustomQuery {
    id: string;
    query: SearchQuery;
    name: string;
    icon: string;
}

export function initCustomQuery(
    query: SearchQuery,
    name: string,
    icon: string,
): CustomQuery {
    return {
        id: uuidv4(),
        query,
        name,
        icon,
    } as CustomQuery;
}

export interface SearchState {
    query: SearchQuery | null;
    queryVersion: number;
    queryError?: string;
    view: SearchView;
    stats: CombinedStats;
    files: {
        [fileId: string]: {
            meta: GetFilesFileEntry;
            preview: GetFilePreviewResponse | null;
        };
    };
    totalFiles: number;
    lastFileSortId: SortId | null;
    filesInView: string[];
    pageNumber: number;
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

const CUSTOM_QUERIES_LOCAL_STORAGE_KEY = "CUSTOM_QUERIES";
export const QUERY_FAILED_FILES = "state:failed";
export const QUERY_CONTENT_TRUNCATED_FILES = "content_truncated:true";

function loadCustomQueries(): CustomQuery[] {
    const data = window.localStorage.getItem(CUSTOM_QUERIES_LOCAL_STORAGE_KEY);
    if (data === null) return [];
    return JSON.parse(data);
}

const initialState: SearchState = {
    query: null,
    queryVersion: 0,
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
    pageNumber: 0,
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
    async (query: SearchQuery, thunkAPI) => {
        const dispatch = thunkAPI.dispatch;
        const lastQuery = (thunkAPI.getState() as RootState).search.query;
        const newQuery = {
            ...lastQuery,
            // By default reset the sortId, but allow it to be overwritten
            // This is to prevent issues with staying on a later page than the new query might have
            sortId: null,
            ...query,
        };
        return await dispatch(applyQuery(newQuery));
    },
);

export const updatePage = createAsyncThunk(
    "updatePageThunk",
    async (sortId: SortId | null, thunkAPI) => {
        const state = thunkAPI.getState() as RootState;
        const dispatch = thunkAPI.dispatch;
        const lastQuery = state.search.query;
        const newQuery = {
            ...lastQuery,
            sortId,
        };
        return await dispatch(applyQuery(newQuery));
    },
);

export const setQuery = createAsyncThunk(
    "setQueryThunk",
    async (query: SearchQuery, thunkAPI) => {
        const dispatch = thunkAPI.dispatch;

        return await dispatch(applyQuery(query));
    },
);

const applyQuery = createAsyncThunk(
    "applyQueryThunk",
    async (query: SearchQuery, thunkAPI) => {
        const dispatch = thunkAPI.dispatch;
        // do not run query if empty
        if (!query.query || query.query.trim().length == 0) {
            return {
                query: query,
            };
        }
        const queryNew: SearchQuery = {
            query: query.query,
            // reset languages to null if there are zero languages
            languages:
                query.languages && query.languages?.length > 0
                    ? query.languages
                    : null,
            sortField: query.sortField,
            sortDirection: query.sortDirection,
            sortId: query.sortId,
            pageSize: query.pageSize ?? defaultPageSize,
        };
        try {
            dispatch(startLoadingIndicator());
            const searchResult = await searchFiles(queryNew);
            return {
                ...searchResult,
                query: queryNew,
            };
        } catch (err: any) {
            return thunkAPI.rejectWithValue(
                err.detail ? err.detail : err.toString(),
            );
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
        const dispatch = thunkAPI.dispatch;
        const searchState = (thunkAPI.getState() as RootState).search;
        const query = searchState.query;
        if (!query) return;
        try {
            const preview = await getFilePreview(fileId, query);
            dispatch(addFilePreview(preview));
        } catch (err: any) {
            dispatch(removeFile(fileId));
            return thunkAPI.rejectWithValue(
                err.detail ? err.detail : err.toString(),
            );
        }
    },
);

export const fetchContentTruncatedFiles = createAsyncThunk(
    "fetchContentTruncatedFilesThunk",
    async () => {
        return searchFiles({
            query: QUERY_CONTENT_TRUNCATED_FILES,
            pageSize: 0,
        });
    },
);

export const fetchFailedFiles = createAsyncThunk(
    "fetchFailedFilesThunk",
    async () => {
        return searchFiles({
            query: QUERY_FAILED_FILES,
            pageSize: 0,
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

function addFileInformation(state: any, action: any) {
    // save last query
    if (!action.payload) return;
    const payload = action.payload.payload;
    state.query = payload.query;
    state.queryVersion++;
    const fileEntriesModel: GetFilesResponse = payload;
    if (!fileEntriesModel.files) return;
    fileEntriesModel.files.forEach((file) => {
        // initialize file in files list
        state.files[file.fileId] = {
            meta: file,
            preview: null,
        };
    });
    state.totalFiles = payload.totalFiles;
    state.lastFileSortId =
        fileEntriesModel.files[fileEntriesModel.files.length - 1]?.sortId;
    state.queryError = undefined;
}

export const searchSlice = createSlice({
    name: "search",
    initialState,
    reducers: {
        setSearchView: (state, action: PayloadAction<SearchView>) => {
            state.view = action.payload;
        },
        addCustomQuery: (state, action: PayloadAction<CustomQuery>) => {
            state.customQueries.push(action.payload);
            window.localStorage.setItem(
                CUSTOM_QUERIES_LOCAL_STORAGE_KEY,
                JSON.stringify(state.customQueries),
            );
        },
        deleteCustomQuery: (state, action: PayloadAction<CustomQuery>) => {
            const toRemove = state.customQueries.find(
                (cq) => cq.id == action.payload.id,
            );

            if (toRemove) {
                const index = state.customQueries.indexOf(toRemove);
                state.customQueries.splice(index, 1);
            }
            window.localStorage.setItem(
                CUSTOM_QUERIES_LOCAL_STORAGE_KEY,
                JSON.stringify(state.customQueries),
            );
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

        incrementPageNumber: (state) => {
            state.pageNumber += 1;
        },
        addFilePreview: (
            state,
            action: PayloadAction<GetFilePreviewResponse>,
        ) => {
            const fileId = action.payload.fileId;
            const file = state.files[fileId];
            if (!file) return;
            file.preview = action.payload;
        },
        removeFile: (state, action: PayloadAction<string>) => {
            const fileId = action.payload;
            delete state.files[fileId];
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
    },
    extraReducers: (builder) => {
        builder.addCase(
            fetchContentTruncatedFiles.fulfilled,
            (state, action) => {
                state.contentTruncatedFilesCount = action.payload.totalFiles;
            },
        );
        builder.addCase(fetchFailedFiles.fulfilled, (state, action) => {
            state.failedFilesCount = action.payload.totalFiles;
        });
        builder.addCase(updatePage.fulfilled, (state, action: any) => {
            addFileInformation(state, action);
        });
        builder.addCase(setQuery.fulfilled, (state, action: any) => {
            // reset files
            state.files = {};
            state.pageNumber = 0;

            addFileInformation(state, action);
        });
        builder.addCase(updateQuery.fulfilled, (state, action: any) => {
            // reset files
            state.files = {};
            state.pageNumber = 0;

            addFileInformation(state, action);
        });
        builder.addCase(applyQuery.rejected, (state, action: any) => {
            const error = action.payload;
            toast.error("Cannot load search results. Error: " + error);

            state.queryError = error;
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
    fillStatsSummary,
    fillStatsTags,
    fillStatsGeneric,
    addFilePreview,
    incrementPageNumber,
    removeFile,
    setTags,
    setLanguages,
    setTranslationLanguage,
    setWebSocketPubSubMessage,
    setDisplayStat,
    setChatbotOpen,
    setSummarizationSystemPrompt,
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

export const selectQueryVersion = createSelector(
    selectSearch,
    (search) => search.queryVersion,
);

export const selectPageNumber = createSelector(
    selectSearch,
    (search) => search.pageNumber,
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
export const selectNumberOfFiles = createSelector(
    selectSearch,
    (search) => search.totalFiles,
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

export default searchSlice.reducer;
