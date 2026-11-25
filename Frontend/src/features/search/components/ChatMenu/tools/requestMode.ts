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
            "'work' — the default: read the corpus, drive the UI, and change files; " +
            "'research' — read the corpus without being able to change anything, plus " +
            "rag_search, which answers a question across the whole corpus in one call. " +
            "Ask for 'research' for questions like 'what do you know about X' or " +
            "'what is the relationship between A and B': rag_search is the only thing " +
            "'work' cannot do, and the trade is every tool that writes.",
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
