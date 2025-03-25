import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RootState } from "../../app/store";
import { ArchiveHit, ArchivesModel } from "../../app/api";

export interface ArchiveState {
    query: string;
    archives: ArchiveHit[];
    numberOfResults: number;
    hasMore: boolean;
    currentPage: number;
}

const initialState: ArchiveState = {
    query: "",
    archives: [],
    numberOfResults: 0,
    hasMore: false,
    currentPage: 0,
};

export const archiveSlice = createSlice({
    name: "archive",
    initialState,
    reducers: {
        fillArchives: (state, action: PayloadAction<ArchivesModel>) => {
            state.archives = action.payload.hits;
            state.currentPage = 0;
            state.hasMore = state.archives.length < action.payload.total;
            state.numberOfResults = action.payload.total;
        },
        removeArchive: (state, action: PayloadAction<string>) => {
            const filteredArchives = state.archives.filter(
                (archive) => archive.fileId !== action.payload,
            );
            return {
                ...state,
                archives: filteredArchives,
            };
        },
    },
});

export const { fillArchives, removeArchive } = archiveSlice.actions;

export const selectArchive = (state: RootState) => state.archive;
export const selectArchives = createSelector(
    selectArchive,
    (archive) => archive.archives,
);
export const selectNumberOfArchives = createSelector(
    selectArchive,
    (archive) => archive.numberOfResults,
);
export const selectHasMoreResults = createSelector(
    selectArchive,
    (archive) => archive.hasMore,
);
export const selectCurrentSearchPage = createSelector(
    selectArchive,
    (archive) => archive.currentPage,
);

export default archiveSlice.reducer;
