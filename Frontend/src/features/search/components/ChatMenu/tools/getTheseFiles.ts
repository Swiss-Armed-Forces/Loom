import type { PassiveFrontendTool, StateAccessor } from "./types";

export const createGetTheseFilesTool = (
    getState: StateAccessor,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "get_these_files",
        description:
            "Return the file IDs of all files currently visible in the search " +
            'results. Use this when the user refers to "these files", ' +
            '"the files I\'m looking at", "current results", or similar.',
        parameters: {
            type: "object",
            properties: {},
        },
    },
    handler: async () => {
        const fileIds = getState().search.filesInView;
        if (!fileIds || fileIds.length === 0) {
            return JSON.stringify({
                error: "No files are currently visible in the search results.",
            });
        }
        return JSON.stringify({ file_ids: fileIds });
    },
});
