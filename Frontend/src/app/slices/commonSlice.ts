import {
    createAsyncThunk,
    createSelector,
    createSlice,
    PayloadAction,
} from "@reduxjs/toolkit";
import { UUIDTypes, v4 as uuidv4 } from "uuid";

import {
    fetchCount,
    fetchOverallQueueStatistics,
    OverallQueuesStats,
} from "@app/api";
import { RootState } from "@app/store";
import { FileDetailTab } from "@features/common/utils/enums";
import { DialogComponent } from "@features/common/utils/model";

export interface DialogProps {
    onClose: () => void;
    id: string;
}

export const DefaultErrorMessage =
    "Oops... Something went wrong. Please reload the page";

export interface CommonState {
    loading: number;
    queueStats: OverallQueuesStats;
    dialogs: DialogComponent[];
    lastFileDetailTab: FileDetailTab;
}
const initialState: CommonState = {
    loading: 0,
    queueStats: {
        messagesInQueues: 0,
        completeEstimateTimestamp: undefined,
        pausedQueuesCount: 0,
    },
    dialogs: [],
    lastFileDetailTab: FileDetailTab.Rendered,
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
        openDialog: (state, action: PayloadAction<DialogComponent>) => {
            const newDialog = {
                ...action.payload,
                id: action.payload.id || uuidv4(),
            };
            state.dialogs.push(newDialog);
        },
        closeDialog: (state, action: PayloadAction<UUIDTypes>) => {
            state.dialogs = state.dialogs.filter(
                (dialog) => dialog.id !== action.payload,
            );
        },
        updateDialogPropsById: (
            state,
            action: PayloadAction<{ id: string; props: Record<string, any> }>,
        ) => {
            const { id, props } = action.payload;
            const dialog = state.dialogs.find((d) => d.id === id);

            if (dialog) {
                dialog.props = {
                    ...(dialog.props || {}),
                    ...props,
                };
            }
        },
        setLastFileDetailTab: (state, action: PayloadAction<FileDetailTab>) => {
            state.lastFileDetailTab = action.payload;
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
    openDialog,
    closeDialog,
    updateDialogPropsById,
    setLastFileDetailTab,
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

export const selectDialogs = createSelector(
    selectCommon,
    (common) => common.dialogs,
);
export const selectTopDialog = createSelector(
    selectCommon,
    (common) => common.dialogs[common.dialogs.length - 1] || undefined,
);

export const selectLastFileDetailTab = createSelector(
    selectCommon,
    (common) => common.lastFileDetailTab,
);

export default commonSlice.reducer;
