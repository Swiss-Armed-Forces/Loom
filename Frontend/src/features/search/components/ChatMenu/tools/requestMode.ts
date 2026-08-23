import type { InteractiveFrontendTool } from "./types";

export const createRequestModeTool = (): InteractiveFrontendTool => ({
    interactive: true,
    definition: {
        name: "request_mode",
        description:
            "Request to switch to a different mode. " +
            "The user will be prompted to confirm before the mode is activated. " +
            "Available modes: " +
            "'chat' — pure conversation with no tool access; " +
            "'work' — default mode with deferred document capabilities; " +
            "'research' — enables full document access (execute_query, get_file, " +
            "get_file_field, rag_search) for comprehensive multi-step research tasks " +
            "such as 'what do you know about X', 'how many files mention Y', " +
            "or 'what is the relationship between A and B'.",
        parameters: {
            type: "object",
            properties: {
                mode: {
                    type: "string",
                    enum: ["chat", "work", "research"],
                    description: "The mode to switch to.",
                },
                reason: {
                    type: "string",
                    description:
                        "Brief explanation of why this mode is needed.",
                },
            },
            required: ["mode", "reason"],
        },
    },
});
