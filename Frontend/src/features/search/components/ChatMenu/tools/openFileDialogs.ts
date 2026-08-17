import { openDialog } from "@app/slices/commonSlice";
import type { AppDispatch } from "@app/store";
import { DialogType } from "@features/common/utils/enums";

import type { PassiveFrontendTool, StateAccessor } from "./types";

export const createOpenFileDialogTools = (
    getState: StateAccessor,
    dispatch: AppDispatch,
): PassiveFrontendTool[] => [
    {
        interactive: false,
        definition: {
            name: "open_add_tags",
            description:
                "Open the tag editor dialog for a specific file, or for bulk tagging " +
                "across the current query (omit file_id). Use this when the user wants " +
                "to add tags to a document.",
            parameters: {
                type: "object",
                properties: {
                    file_id: {
                        type: "string",
                        description:
                            "The ID of the file to tag. Omit for bulk tagging on the " +
                            "current query.",
                    },
                },
            },
        },
        handler: async (args) => {
            const fileId = args.file_id ? String(args.file_id) : undefined;
            const filePreview = fileId
                ? (getState().search.files[fileId]?.preview ?? undefined)
                : undefined;
            if (fileId && !filePreview) {
                return JSON.stringify({
                    error:
                        "File preview not loaded. Ask the user to open the file first, " +
                        "or omit file_id for bulk tagging.",
                });
            }
            dispatch(
                openDialog({
                    id: "",
                    type: DialogType.AddTagsDialog,
                    props: { filePreview },
                }),
            );
            return JSON.stringify({ success: true });
        },
    },
];
