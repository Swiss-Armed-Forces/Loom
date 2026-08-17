import type { InteractiveFrontendTool } from "./types";

export const createAskUserTool = (): InteractiveFrontendTool => ({
    interactive: true,
    definition: {
        name: "ask_user",
        description:
            "Ask the user a clarifying question with a fixed set of answer options. " +
            "Use this when you need to know the user's preference before proceeding, " +
            "e.g. whether to search broadly or narrowly, which date range to focus on, " +
            "or which type of documents to prioritise. The user will see the question " +
            "and clickable answer chips; their selection is returned as the tool result.",
        parameters: {
            type: "object",
            properties: {
                question: {
                    type: "string",
                    description: "The question to display to the user.",
                },
                options: {
                    type: "array",
                    items: { type: "string" },
                    description:
                        "The answer choices to present as clickable chips.",
                },
            },
            required: ["question", "options"],
        },
    },
});
