import { CapabilityId } from "@app/api/generated";
import {
    bumpHighlightScroll,
    setHighlightedFileId,
} from "@app/slices/searchSlice";
import type { AppDispatch } from "@app/store";

import { toolError, toolSuccess, type PassiveFrontendTool } from "./types";

export const createHighlightFileTool = (
    dispatch: AppDispatch,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "highlight_file",
        capabilities: [CapabilityId.UiInteraction],
        description:
            "Scroll to and visually highlight a file card in the results list without " +
            "opening it in the detail panel. Use this to point out a specific document " +
            "to the user. Requires a file_id obtained from read_state.",
        parameters: {
            type: "object",
            properties: {
                file_id: {
                    type: "string",
                    description: "The ID of the file to highlight.",
                },
            },
            required: ["file_id"],
        },
    },
    handler: async (args) => {
        const fileId = String(args.file_id ?? "");
        if (!fileId) return toolError("file_id required");
        dispatch(setHighlightedFileId(fileId));
        dispatch(bumpHighlightScroll());
        return toolSuccess();
    },
});
