import type { InteractiveFrontendTool } from "./types";

export const createRequestCapabilityTool = (): InteractiveFrontendTool => ({
    interactive: true,
    definition: {
        name: "request_capability",
        description:
            "Request to enable an extended capability. " +
            "Use this when the user's question requires abilities beyond the default set. " +
            "The user will be prompted to confirm before the capability is activated. " +
            "Available capabilities: " +
            "'research_mode' — enables full document access (execute_query, get_file, " +
            "get_file_field, rag_search) for comprehensive multi-step research tasks " +
            "such as 'what do you know about X', 'how many files mention Y', " +
            "or 'what is the relationship between A and B'.",
        parameters: {
            type: "object",
            properties: {
                capability: {
                    type: "string",
                    enum: ["research_mode"],
                    description: "The capability to enable.",
                },
                reason: {
                    type: "string",
                    description:
                        "Brief explanation of why this capability is needed.",
                },
            },
            required: ["capability", "reason"],
        },
    },
});
