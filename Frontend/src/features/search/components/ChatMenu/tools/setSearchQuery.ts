import { updateQuery } from "@app/slices/searchSlice";
import type { AppDispatch } from "@app/store";
import { isSortDirection } from "@features/common/utils/model";

import type { StateAccessor } from "./types";
import type { PassiveFrontendTool } from "./types";

export const createSetSearchQueryTool = (
    _getState: StateAccessor,
    dispatch: AppDispatch,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "set_search_query",
        description:
            "Update the active search query in the UI. The results panel will " +
            "immediately refresh to show matching documents. Optionally set sort " +
            "field and direction. Use this when the user asks you to search for " +
            "something or filter the document list.",
        parameters: {
            type: "object",
            properties: {
                query: {
                    type: "string",
                    description: "The search query string to apply.",
                },
                sort_field: {
                    type: "string",
                    description:
                        "Optional field to sort by (e.g. 'date', 'filename'). Omit to keep current.",
                },
                sort_direction: {
                    type: "string",
                    enum: ["asc", "desc"],
                    description: "Sort direction. Omit to keep current.",
                },
            },
            required: ["query"],
        },
    },
    handler: async (args) => {
        const sortDirectionRaw = String(args.sort_direction ?? "");
        dispatch(
            updateQuery({
                query: String(args.query ?? ""),
                sortField: args.sort_field
                    ? String(args.sort_field)
                    : undefined,
                sortDirection: isSortDirection(sortDirectionRaw)
                    ? sortDirectionRaw
                    : undefined,
            }),
        );
        return JSON.stringify({
            success: true,
            message: "Search query updated.",
        });
    },
});
