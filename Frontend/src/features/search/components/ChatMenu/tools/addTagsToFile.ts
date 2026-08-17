import { addTagsToFile as addTagsToFileApi } from "@app/api";
import { setFilePreview } from "@app/slices/searchSlice";
import type { AppDispatch } from "@app/store";

import type { PassiveFrontendTool, StateAccessor } from "./types";

export const createAddTagsToFileTool = (
    getState: StateAccessor,
    dispatch: AppDispatch,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "add_tags_to_file",
        description:
            "Add one or more tags to a specific file. The tags will be immediately " +
            "visible in the UI. Use this when the user asks you to tag or label a " +
            "document.",
        parameters: {
            type: "object",
            properties: {
                file_id: {
                    type: "string",
                    description: "The ID of the file to tag.",
                },
                tags: {
                    type: "array",
                    items: { type: "string" },
                    description: "List of tag names to add to the file.",
                },
            },
            required: ["file_id", "tags"],
        },
    },
    handler: async (args) => {
        const fileId = String(args.file_id ?? "");
        const tags = Array.isArray(args.tags) ? (args.tags as string[]) : [];
        if (!fileId) return JSON.stringify({ error: "file_id required" });
        if (tags.length === 0) {
            return JSON.stringify({ error: "tags array required" });
        }

        try {
            await addTagsToFileApi(fileId, tags);
            const preview = getState().search.files[fileId]?.preview;
            if (preview) {
                dispatch(
                    setFilePreview({
                        ...preview,
                        tags: [...new Set([...(preview.tags ?? []), ...tags])],
                    }),
                );
            }
            return JSON.stringify({ success: true, tagsAdded: tags });
        } catch (e: unknown) {
            return JSON.stringify({ error: String(e) });
        }
    },
});
