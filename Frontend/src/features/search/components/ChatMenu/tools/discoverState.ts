import { ARCHIVE_STATE_DOCS } from "@app/slices/archiveSlice";
import { COMMON_STATE_DOCS } from "@app/slices/commonSlice";
import { SEARCH_STATE_DOCS } from "@app/slices/searchSlice";

import type { PassiveFrontendTool } from "./types";

const STATE_SCHEMA = {
    search: SEARCH_STATE_DOCS,
    common: COMMON_STATE_DOCS,
    archive: ARCHIVE_STATE_DOCS,
};

export const createDiscoverStateTool = (): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "discover_state",
        description:
            "Get a schema of the UI state of the user you are talking to. " +
            "Returns slice names, field names, and type annotations describing " +
            "what the user is currently seeing — their active search query, which " +
            "files are visible, which file tabs are open, etc. Use this to " +
            "understand the user's current context before answering questions that " +
            "depend on what they are looking at. Call this first, then use " +
            "read_state to fetch specific values.",
        parameters: {
            type: "object",
            properties: {},
        },
    },
    handler: async () => JSON.stringify(STATE_SCHEMA),
});
