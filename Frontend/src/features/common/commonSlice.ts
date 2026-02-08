import {
    createAsyncThunk,
    createSelector,
    createSlice,
} from "@reduxjs/toolkit";
import { RootState } from "../../app/store";
import {
    fetchCount,
    fetchOverallQueueStatistics,
    OverallQueuesStats,
} from "../../app/api";

export const DefaultErrorMessage =
    "Oops... Something went wrong. Please reload the page";

export interface CommonState {
    loading: number;
    queueStats: OverallQueuesStats;
}

const initialState: CommonState = {
    loading: 0,
    queueStats: {
        messagesInQueues: 0,
        completeEstimateTimestamp: undefined,
    },
};

export const loadConfigAsync = createAsyncThunk(
    "common/loadConfig",
    async () => {
        const response = await fetchCount();
        return response.data;
    },
);

export const fetchQueueStatistics = createAsyncThunk(
    "fetchQueueStatistics",
    async () => {
        return await fetchOverallQueueStatistics();
    },
);

export const commonSlice = createSlice({
    name: "common",
    initialState,
    reducers: {
        setBackgroundTaskSpinnerActive: (state) => {
            if (state.queueStats.messagesInQueues === 0) {
                state.queueStats.messagesInQueues = 1;
            }
        },
        startLoadingIndicator: (state) => {
            state.loading += 1;
        },
        stopLoadingIndicator: (state) => {
            state.loading -= 1;
        },
    },
    extraReducers: (builder) => {
        builder.addCase(fetchQueueStatistics.fulfilled, (state, action) => {
            state.queueStats = action.payload;
        });
        builder
            .addCase(loadConfigAsync.pending, (state) => {
                state.loading += 1;
            })
            .addCase(loadConfigAsync.fulfilled, (state) => {
                state.loading -= 1;
            })
            .addCase(loadConfigAsync.rejected, (state) => {
                state.loading -= 1;
            });
    },
});

export const {
    setBackgroundTaskSpinnerActive,
    startLoadingIndicator,
    stopLoadingIndicator,
} = commonSlice.actions;

export const selectCommon = (state: RootState) => state.common;
export const selectIsLoading = createSelector(
    selectCommon,
    (common) => common.loading > 0,
);

export const selectQueuesStatistics = createSelector(
    selectCommon,
    (common) => common.queueStats,
);

export default commonSlice.reducer;
