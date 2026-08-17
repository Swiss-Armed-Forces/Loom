import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import { ArchiveHit, ArchivesModel } from "@app/api";
import { RootState } from "@app/store";

export interface ArchiveState {
    query: string;
    archives: ArchiveHit[];
    numberOfResults: number;
    hasMore: boolean;
    currentPage: number;
}

export const ARCHIVE_STATE_DOCS = {
    query: "string — archive search query",
    archives: "ArchiveHit[] — archive search results",
    numberOfResults: "number — total archive count",
    hasMore: "boolean — whether more pages are available",
    currentPage: "number — current pagination page (0-indexed)",
} satisfies Record<keyof ArchiveState, string>;

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
