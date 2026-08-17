import {
    bumpHighlightScroll,
    openFileTabThunk,
    setHighlightedFileId,
} from "@app/slices/searchSlice";
import type { AppDispatch } from "@app/store";
import { FileDetailTab } from "@features/common/utils/enums";

import type { PassiveFrontendTool } from "./types";

export const createNavigateToFileTool = (
    dispatch: AppDispatch,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "navigate_to_file",
        description:
            "Open a file in the detail panel and optionally highlight its card in the " +
            "results list. Use this when the user asks you to open, inspect, or show " +
            "a specific document. Requires a file_id obtained from read_state.",
        parameters: {
            type: "object",
            properties: {
                file_id: {
                    type: "string",
                    description: "The ID of the file to open.",
                },
                detail_tab: {
                    type: "number",
                    description:
                        "Which detail tab to open (0=Rendered, 1=Content, 2=Highlights, " +
                        "3=RAW, 4=Summary, 5=Translations, 6=ImageDescription, 7=Tasks). " +
                        "Defaults to 0 (Rendered).",
                },
                highlight: {
                    type: "boolean",
                    description:
                        "Whether to highlight and scroll to the file card. Defaults to true.",
                },
            },
            required: ["file_id"],
        },
    },
    handler: async (args) => {
        const fileId = String(args.file_id ?? "");
        if (!fileId) return JSON.stringify({ error: "file_id required" });
        const detailTab =
            typeof args.detail_tab === "number"
                ? (args.detail_tab as (typeof FileDetailTab)[keyof typeof FileDetailTab])
                : FileDetailTab.Rendered;
        dispatch(openFileTabThunk({ fileId, detailTab }));
        if (args.highlight !== false) {
            dispatch(setHighlightedFileId(fileId));
            dispatch(bumpHighlightScroll());
        }
        return JSON.stringify({ success: true });
    },
});
