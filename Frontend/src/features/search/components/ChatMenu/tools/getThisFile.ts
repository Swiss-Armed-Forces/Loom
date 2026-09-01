import { CapabilityId } from "@app/api/generated";

import type { PassiveFrontendTool, StateAccessor } from "./types";
import { toolError, toolSuccess } from "./types";

export const createGetThisFileTool = (
    getState: StateAccessor,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "get_this_file",
        capabilities: [CapabilityId.FileAccess],
        description:
            "Return the file ID of the currently highlighted file in the search " +
            'results. Use this as a shorthand when the user refers to "this file", ' +
            '"the current file", "this document", or similar, before calling ' +
            "get_file or any enrichment tool.",
        parameters: {
            type: "object",
            properties: {},
        },
    },
    handler: async () => {
        const fileId = getState().search.highlightedFileId;
        if (!fileId) {
            return toolError("No file is currently highlighted.");
        }
        return toolSuccess({ file_id: fileId });
    },
});
