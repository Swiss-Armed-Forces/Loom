import { CapabilityId } from "@app/api/generated";
import {
    selectFilesInViewOrdered,
    selectOrderedFileIds,
    selectTotalFiles,
} from "@app/slices/searchSlice";

import type { PassiveFrontendTool, StateAccessor } from "./types";
import { toolError, toolSuccess } from "./types";

/**
 * Most the model is handed in one answer.
 *
 * The result list grows on its own as the user scrolls, so without a cap this
 * answer is unbounded. Matches readState's MAX_ARRAY_ITEMS philosophy: report
 * the truncation rather than quietly shortening the list.
 */
const MAX_FILE_IDS = 100;

export const createGetTheseFilesTool = (
    getState: StateAccessor,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "get_these_files",
        capabilities: [CapabilityId.FileAccess],
        description:
            "Return the file IDs of the search results the user currently has " +
            'loaded. Use this when the user refers to "these files", ' +
            '"the files I\'m looking at", "current results", or similar. ' +
            "`file_ids` is the loaded result list in ranking order; " +
            "`visible_file_ids` is the few of those actually on screen right " +
            "now, for when the user means the one they are looking at.",
        parameters: {
            type: "object",
            properties: {},
        },
    },
    handler: async () => {
        const state = getState();
        // The loaded results rather than the viewport: the result list is
        // windowed, so only a handful of cards are mounted at any moment and a
        // viewport answer would change with the scroll position.
        const loaded = selectOrderedFileIds(state);
        if (loaded.length === 0) {
            return toolError("There are no search results loaded.");
        }
        return toolSuccess({
            file_ids: loaded.slice(0, MAX_FILE_IDS),
            truncated: loaded.length > MAX_FILE_IDS,
            loaded_count: loaded.length,
            total_files: selectTotalFiles(state),
            visible_file_ids: selectFilesInViewOrdered(state),
        });
    },
});
