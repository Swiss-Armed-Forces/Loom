import { CapabilityId } from "@app/api/generated";

import type { PassiveFrontendTool, StateAccessor } from "./types";
import { toolError, toolSuccess } from "./types";

export const createGetTheseFilesTool = (
    getState: StateAccessor,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "get_these_files",
        capabilities: [CapabilityId.FileAccess],
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
            return toolError(
                "No files are currently visible in the search results.",
            );
        }
        return toolSuccess({ file_ids: fileIds });
    },
});
