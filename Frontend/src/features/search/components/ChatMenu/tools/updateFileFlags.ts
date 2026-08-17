import { updateFile } from "@app/api";
import type { UpdateFileRequest } from "@app/api/generated/models/UpdateFileRequest";
import { setFilePreview } from "@app/slices/searchSlice";
import type { AppDispatch } from "@app/store";

import type { PassiveFrontendTool, StateAccessor } from "./types";

export const createUpdateFileFlagsTool = (
    getState: StateAccessor,
    dispatch: AppDispatch,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "update_file_flags",
        description:
            "Update one or more boolean flags on a file: seen, flagged, or hidden. " +
            "At least one flag must be provided. Use this when the user asks you to " +
            "mark a file as seen/unseen, flag/unflag it, or hide/unhide it.",
        parameters: {
            type: "object",
            properties: {
                file_id: {
                    type: "string",
                    description: "The ID of the file to update.",
                },
                seen: {
                    type: "boolean",
                    description:
                        "Mark the file as seen (true) or unseen (false).",
                },
                flagged: {
                    type: "boolean",
                    description: "Flag (true) or unflag (false) the file.",
                },
                hidden: {
                    type: "boolean",
                    description: "Hide (true) or unhide (false) the file.",
                },
            },
            required: ["file_id"],
        },
    },
    handler: async (args) => {
        const fileId = String(args.file_id ?? "");
        if (!fileId) return JSON.stringify({ error: "file_id required" });

        const request: UpdateFileRequest = {};
        if (typeof args.seen === "boolean") request.seen = args.seen;
        if (typeof args.flagged === "boolean") request.flagged = args.flagged;
        if (typeof args.hidden === "boolean") request.hidden = args.hidden;
        if (Object.keys(request).length === 0) {
            return JSON.stringify({
                error: "At least one of seen/flagged/hidden required.",
            });
        }

        try {
            await updateFile(fileId, request);
            const preview = getState().search.files[fileId]?.preview;
            if (preview) {
                dispatch(setFilePreview({ ...preview, ...request }));
            }
            return JSON.stringify({ success: true });
        } catch (e: unknown) {
            return JSON.stringify({ error: String(e) });
        }
    },
});
