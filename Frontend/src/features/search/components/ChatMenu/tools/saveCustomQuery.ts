import { addCustomQuery, initCustomQuery } from "@app/slices/searchSlice";
import type { AppDispatch } from "@app/store";

import type { PassiveFrontendTool, StateAccessor } from "./types";

export const createSaveCustomQueryTool = (
    getState: StateAccessor,
    dispatch: AppDispatch,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "save_custom_query",
        description:
            "Save the current search query as a named shortcut in the left sidebar so " +
            "the user can quickly rerun it later. Requires an active search query. " +
            "Use this when the user says they want to bookmark or save the current search.",
        parameters: {
            type: "object",
            properties: {
                name: {
                    type: "string",
                    description: "Display name for the saved query.",
                },
                icon: {
                    type: "string",
                    description:
                        "Material icon name for the shortcut (e.g. 'Tune', 'Search', 'Star'). " +
                        "Defaults to 'Tune'.",
                },
            },
            required: ["name"],
        },
    },
    handler: async (args) => {
        const state = getState();
        const query = state.search.query;
        if (!query) {
            return JSON.stringify({ error: "No active search query to save." });
        }
        const name = String(args.name ?? "").trim();
        if (!name) return JSON.stringify({ error: "name required" });
        const icon = String(args.icon ?? "Tune");
        dispatch(
            addCustomQuery(
                initCustomQuery(query, state.search.totalFiles, name, icon),
            ),
        );
        return JSON.stringify({ success: true, name });
    },
});
