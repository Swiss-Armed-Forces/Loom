import { CapabilityId } from "@app/api/generated";
import { closeFileTabThunk } from "@app/slices/searchSlice";
import type { AppDispatch } from "@app/store";

import { toolError, toolSuccess, type PassiveFrontendTool } from "./types";

export const createCloseFileTool = (
    dispatch: AppDispatch,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "close_file",
        capabilities: [CapabilityId.UiInteraction],
        description:
            "Close a single file tab in the detail panel. Use this only when the " +
            "user wants to close a specific document.",
        parameters: {
            type: "object",
            properties: {
                file_id: {
                    type: "string",
                    description: "The ID of the file to close.",
                },
            },
            required: ["file_id"],
        },
    },
    handler: async (args) => {
        const fileId = String(args.file_id ?? "");
        if (!fileId) return toolError("file_id required");

        dispatch(closeFileTabThunk(fileId));

        return toolSuccess();
    },
});
